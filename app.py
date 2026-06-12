import asyncio
import logging

from pyrogram import Client, idle

from utils import chats, state
from utils.config import API_ID, API_HASH, BOT_TOKEN, CHATS_FILE, PERSONAS_FILE

logging.basicConfig(level=logging.WARNING, format="%(name)s %(levelname)s %(message)s")
logging.getLogger("utils.ai").setLevel(logging.INFO)

app = Client(
    "small_ai_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
)

async def _main():
    chats.init(CHATS_FILE)
    state.load_personas(PERSONAS_FILE)

    await app.start()
    me = await app.get_me()
    state.set_bot_name(me.first_name)
    logging.warning("Bot started as %s", me.first_name)

    await idle()
    await app.stop()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(_main())
