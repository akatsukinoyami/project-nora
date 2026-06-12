import asyncio
import logging
import random
import re

import yaml
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction
from pyrogram.types import Message

from utils.ai import ask
from utils.config import (
  API_ID, 
  API_HASH, 
  BOT_TOKEN, 
  PERSONAS_FILE, 
  PERSONA_KEY, 
  RANDOM_REPLY_CHANCE
)

def _load_persona() -> str:
    with open(PERSONAS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    base = data.get("base_instructions", "")
    return data[PERSONA_KEY]["system"] + ("\n" + base if base else "")


SYSTEM = _load_persona()

logging.basicConfig(level=logging.WARNING, format="%(name)s %(levelname)s %(message)s")
logging.getLogger("utils.ai").setLevel(logging.INFO)

app = Client("small_ai_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

_bot_name: str | None = None

reply_to_me = filters.create(
    lambda _, __, m: bool(m.reply_to_message and m.reply_to_message.from_user.is_self)
)
name_called = filters.create(
    lambda _, __, m: bool(
        _bot_name
        and m.text
        and re.search(rf"(?i)\b{re.escape(_bot_name)},", m.text)
    )
)
random_nudge = filters.create(
    lambda _, __, m: not m.chat.type.value.startswith("private")
    and random.random() < RANDOM_REPLY_CHANCE
)

filter_answer = filters.mentioned | reply_to_me | filters.private | name_called | random_nudge
message_type = filters.text | filters.photo | filters.sticker | filters.animation | filters.video


async def keep_typing(client: Client, chat_id: int, stop: asyncio.Event):
    while not stop.is_set():
        try:
            await client.send_chat_action(chat_id, ChatAction.TYPING)
        except Exception as e:
            logging.error("send_chat_action failed: %s", e)
        try:
            await asyncio.wait_for(asyncio.shield(stop.wait()), timeout=4.0)
        except asyncio.TimeoutError:
            pass


@app.on_message(filters.command("ping"))
async def on_ping(_client: Client, message: Message):
    await message.reply("Pong 🏓")


@app.on_message(message_type & filter_answer & ~filters.bot)
async def on_reply(client: Client, message: Message):
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    stop = asyncio.Event()
    asyncio.create_task(keep_typing(client, message.chat.id, stop))
    try:
        text = await ask(SYSTEM, message, reply_to=message.reply_to_message)
    finally:
        stop.set()
    await message.reply(text)


async def _main():
    global _bot_name
    await app.start()
    me = await app.get_me()
    _bot_name = me.first_name
    logging.warning("Bot started as %s", _bot_name)
    await idle()
    await app.stop()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(_main())
