import asyncio
import random
import re

from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message

from utils import state
from utils.ai import ask, ask_media_group, history_text
from utils.config import ALLOWED_USERS, RANDOM_REPLY_CHANCE

_seen_groups: set[str] = set()


def _is_admin_private(message: Message) -> bool:
    return (
        message.chat.type.value.startswith("private")
        and bool(message.from_user and message.from_user.id in ALLOWED_USERS)
    )


async def _keep_typing(client: Client, chat_id: int, stop: asyncio.Event):
    while not stop.is_set():
        try:
            await client.send_chat_action(chat_id, ChatAction.TYPING)
        except Exception:
            pass
        try:
            await asyncio.wait_for(asyncio.shield(stop.wait()), timeout=4.0)
        except asyncio.TimeoutError:
            pass


async def _send(message: Message, text: str) -> Message:
    try:
        return await message.reply(text)
    except Exception as e:
        if "MESSAGE_EMPTY" in str(e):
            return await message.reply("*нарочито молчит*")
        else:
            raise


reply_to_me = filters.create(
    lambda _, __, m: bool(
        m.reply_to_message
        and m.reply_to_message.from_user
        and m.reply_to_message.from_user.is_self
    )
)
name_called = filters.create(
    lambda _, client, m: bool(
        getattr(client, "bot_name", None)
        and m.text
        and re.search(rf"(?i)(?<!\w){re.escape(client.bot_name)},", m.text)
    )
)
chat_allowed = filters.create(
    lambda _, client, m: getattr(client, "chats", None) and client.chats.is_allowed(m.chat.id)
    or (m.from_user and m.from_user.id in ALLOWED_USERS)
)
random_nudge = filters.create(
    lambda _, __, m: not m.chat.type.value.startswith("private")
    and random.random() < RANDOM_REPLY_CHANCE
)

_trigger = filters.mentioned | reply_to_me | filters.private | name_called | random_nudge
_media = filters.text | filters.photo | filters.sticker | filters.animation | filters.video


@Client.on_message(_media & chat_allowed, group=1)
async def on_history(client: Client, message: Message):
    if message.from_user and message.from_user.is_self:
        return
    try:
        text = await history_text(message)
    except Exception:
        text = message.text or message.caption or ""
    client.chats.add_history(message.chat.id, message.id, "user", text)


@Client.on_message(_media & filters.media_group & _trigger & chat_allowed & ~filters.bot)
async def on_media_group(client: Client, message: Message):
    gid = message.media_group_id
    if gid in _seen_groups:
        return
    _seen_groups.add(gid)

    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    stop = asyncio.Event()
    asyncio.create_task(_keep_typing(client, message.chat.id, stop))

    client.chats.record_call(message)

    try:
        group_messages = await client.get_media_group(message.chat.id, message.id)
    except Exception:
        group_messages = [message]

    persona_key = client.chats.get_persona(message.chat.id) or client.default_persona
    system = state.get_system(persona_key)

    try:
        debug = client.debug_vision and _is_admin_private(message)
        text = await ask_media_group(
            system, group_messages, reply_to=message.reply_to_message, debug=debug, chats=client.chats
        )
    finally:
        stop.set()

    sent = await _send(message, text)
    client.chats.add_history(message.chat.id, sent.id, "assistant", text)


@Client.on_message(_media & ~filters.media_group & _trigger & chat_allowed & ~filters.bot)
async def on_reply(client: Client, message: Message):
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    stop = asyncio.Event()
    asyncio.create_task(_keep_typing(client, message.chat.id, stop))

    client.chats.record_call(message)

    persona_key = client.chats.get_persona(message.chat.id) or client.default_persona
    system = state.get_system(persona_key)

    try:
        debug = client.debug_vision and _is_admin_private(message)
        text = await ask(
            system, message, reply_to=message.reply_to_message, debug=debug, chats=client.chats
        )
    finally:
        stop.set()

    sent = await _send(message, text)
    client.chats.add_history(message.chat.id, sent.id, "assistant", text)
