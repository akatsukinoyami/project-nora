import asyncio
import random
import re

from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message

from utils import state
from utils.ai import ask
from utils.config import ALLOWED_USERS, RANDOM_REPLY_CHANCE


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


@Client.on_message(_media & _trigger & chat_allowed & ~filters.bot)
async def on_reply(client: Client, message: Message):
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    stop = asyncio.Event()
    asyncio.create_task(_keep_typing(client, message.chat.id, stop))

    client.chats.record_call(message)

    persona_key = client.chats.get_persona(message.chat.id) or client.default_persona
    system = state.get_system(persona_key)

    try:
        debug = client.debug_vision and _is_admin_private(message)
        text = await ask(system, message, reply_to=message.reply_to_message, debug=debug)
    finally:
        stop.set()

    try:
        await message.reply(text)
    except Exception as e:
        if "MESSAGE_EMPTY" in str(e):
            await message.reply("*нарочито молчит*")
        else:
            raise
