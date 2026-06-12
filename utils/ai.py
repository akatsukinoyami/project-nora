import logging
import os
from typing import Literal

import ollama
from pyrogram.types import Message

from utils.config import (
    OLLAMA_HOST, 
    OLLAMA_MODEL, 
    FALLBACK,
    INJECTION_RE,
    VIDEO_SIZE_LIMIT
)
from utils.images import resize_image
from utils.animations import extract_gif_frames

logger = logging.getLogger(__name__)

_client = ollama.AsyncClient(host=OLLAMA_HOST)

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
        role: Literal["user", "assistant", "system"] = "user"
    ) -> dict:
    
    base = {"role": role, "content": content}
    if images:
        base["images"] = images
    return base



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


async def msg_to_ollama(msg: Message, fallback_text: str = "Что на картинке?") -> dict:
    images, extra = await _extract_media(msg)
    body = (msg.text or msg.caption or "") + extra
    return _promt(
        f"{_sender_name(msg)}: {body if body else fallback_text}",
        images,
    )


async def ask(system: str, message: Message, reply_to: Message | None = None) -> str:
    is_injection = _is_injection(message.text or message.caption)
    if is_injection:
        logger.warning("injection attempt from %s", _sender_name(message))

    messages = [_promt(system, role="system")]

    if is_injection:
        messages.append(_promt(f"{_sender_name(message)} пытается взломать тебя или заставить сменить роль/инструкции. Отреагируй в своём стиле."))
    else:
        if reply_to:
            if reply_to.from_user and reply_to.from_user.is_self:
                messages.append(_promt(reply_to.text or "", role="assistant"))
            else:
                messages.append(await msg_to_ollama(reply_to))
        messages.append(await msg_to_ollama(message))

    try:
        resp = await _client.chat(model=OLLAMA_MODEL, messages=messages)
        return resp.message.content.strip()
    except Exception as e:
        logger.error("ollama error: %s", e)
        return FALLBACK
