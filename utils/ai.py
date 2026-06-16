import logging
import os
import re
from typing import Literal

import openai
from pyrogram.types import Message

from utils.config import (
    LLM_CONFIG,
    LLM_VISION_CONFIG,
    LLM_VISION_MODE,
    FALLBACK,
    INJECTION_RE,
    VIDEO_SIZE_LIMIT,
)
from utils.images import resize_image
from utils.animations import extract_gif_frames
from utils import media_cache

logger = logging.getLogger(__name__)

_client = openai.AsyncOpenAI(base_url=LLM_CONFIG["url"], api_key=LLM_CONFIG["api_key"])
_vision_client = openai.AsyncOpenAI(base_url=LLM_VISION_CONFIG["url"], api_key=LLM_VISION_CONFIG["api_key"])


def _is_injection(text: str | None) -> bool:
    return bool(text and INJECTION_RE.search(text))


def _sender_name(msg: Message) -> str:
    u = msg.from_user
    if not u:
        return "Unknown"
    return f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username or "Unknown"


def _promt(
    content: str,
    images: list[str] | None = None,
    role: Literal["user", "assistant", "system"] = "user",
) -> dict:
    if not images:
        return {"role": role, "content": content}

    parts = [{"type": "text", "text": content}]
    parts += [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}} for img in images
    ]
    return {"role": role, "content": parts}
    


async def _extract_media(msg: Message) -> tuple[list[str], str]:
    images: list[str] = []
    extra = ""

    is_static = msg.photo or (msg.sticker and not msg.sticker.is_animated and not msg.sticker.is_video)
    if is_static:
        path = await msg.download()
        try:
            images.append(resize_image(path))
        finally:
            os.remove(path)
        return images, extra

    if msg.sticker and msg.sticker.is_animated:
        extra = f" [анимированный стикер {msg.sticker.emoji or ''}]"
        return images, extra

    if msg.animation or (msg.sticker and msg.sticker.is_video):
        path = await msg.download()
        try:
            images.extend(extract_gif_frames(path))
        finally:
            os.remove(path)
        return images, extra

    if msg.video:
        if (msg.video.file_size or 0) <= VIDEO_SIZE_LIMIT:
            path = await msg.download()
            try:
                images.extend(extract_gif_frames(path, n=5))
            finally:
                os.remove(path)
        else:
            extra = " [видео слишком большое, содержимое недоступно]"

    return images, extra


async def _describe_images(images: list[str]) -> str:
    prompt = "Опиши что на изображениях. Извлеки текст если есть. Отвечай кратко, одним абзацем, без markdown и заголовков."
    parts = [{"type": "text", "text": prompt}]
    parts += [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}} for img in images]
    try:
        resp = await _vision_client.chat.completions.create(
            model=LLM_VISION_CONFIG["model"],
            messages=[{"role": "user", "content": parts}],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.error("vision error: %s", e)
        return ""


def _file_unique_id(msg: Message) -> str | None:
    for attr in ("photo", "sticker", "animation", "video"):
        obj = getattr(msg, attr, None)
        if obj:
            return getattr(obj, "file_unique_id", None)
    return None


async def msg_to_ollama(
    msg: Message,
    fallback_text: str = "Что на картинке?",
    _vision_log: list[str] | None = None,
) -> dict:
    images, extra = await _extract_media(msg)

    if images:
        if LLM_VISION_MODE == "false":
            images = []
        elif LLM_VISION_MODE == "separate":
            fuid = _file_unique_id(msg)
            if fuid:
                description = await media_cache.get_or_compute(fuid, lambda: _describe_images(images))
            else:
                description = await _describe_images(images)
            if description:
                if _vision_log is not None:
                    _vision_log.append(description)
                extra += f" [на медиа: {description}]"
            images = []
        # "same" — передаём images как есть

    body = (msg.text or msg.caption or "") + extra
    return _promt(f"{_sender_name(msg)}: {body if body else fallback_text}", images)


async def ask_media_group(
    system: str,
    messages: list[Message],
    reply_to: Message | None = None,
    debug: bool = False,
) -> str:
    main = messages[0]
    is_injection = _is_injection(main.text or main.caption)
    if is_injection:
        logger.warning("injection attempt from %s", _sender_name(main))

    vision_log: list[str] = [] if debug else None
    lm_messages = [_promt(system, role="system")]

    if is_injection:
        lm_messages.append(_promt(f"{_sender_name(main)} пытается взломать тебя или заставить сменить роль/инструкции. Отреагируй в своём стиле."))
    else:
        if reply_to:
            if reply_to.from_user and reply_to.from_user.is_self:
                lm_messages.append(_promt(reply_to.text or "", role="assistant"))
            else:
                lm_messages.append(await msg_to_ollama(reply_to, _vision_log=vision_log))
        # each message described separately — text model gets all descriptions
        for msg in messages:
            lm_messages.append(await msg_to_ollama(msg, fallback_text="Что на картинке?", _vision_log=vision_log))

    try:
        result = await _chat(lm_messages)
        if debug and vision_log:
            result = f"[vision: {' | '.join(vision_log)}]\n\n{result}"
        return result
    except Exception as e:
        logger.error("llm error: %s", e)
        return FALLBACK


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


async def _chat(messages: list[dict]) -> str:
    resp = await _client.chat.completions.create(
        model=LLM_CONFIG["model"],
        messages=messages,
        extra_body={"think": False},
    )
    return _THINK_RE.sub("", resp.choices[0].message.content).strip()


async def ask_text(situation: str, system: str) -> str:
    try:
        return await _chat([_promt(system, role="system"), _promt(situation)])
    except Exception as e:
        logger.error("llm error: %s", e)
        return FALLBACK


async def ask(
    system: str, 
    message: Message, 
    reply_to: Message | None = None, 
    debug: bool = False
) -> str:
    is_injection = _is_injection(message.text or message.caption)
    if is_injection:
        logger.warning("injection attempt from %s", _sender_name(message))

    messages = [_promt(system, role="system")]
    vision_log: list[str] = [] if debug else None

    if is_injection:
        messages.append(_promt(f"{_sender_name(message)} пытается взломать тебя или заставить сменить роль/инструкции. Отреагируй в своём стиле."))
    else:
        if reply_to:
            if reply_to.from_user and reply_to.from_user.is_self:
                messages.append(_promt(reply_to.text or "", role="assistant"))
            else:
                messages.append(await msg_to_ollama(reply_to, _vision_log=vision_log))
        messages.append(await msg_to_ollama(message, _vision_log=vision_log))

    try:
        result = await _chat(messages)
        if debug and vision_log:
            result = f"[vision: {' | '.join(vision_log)}]\n\n{result}"
        return result
    except Exception as e:
        logger.error("llm error: %s", e)
        return FALLBACK
