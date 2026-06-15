import asyncio
import logging
import os

from pyrogram import Client, idle

from utils import chats, state
from utils.config import PYROGRAM_CONFIG, CHATS_FILE, PERSONAS_DIR

logging.basicConfig(level=logging.WARNING, format="%(name)s %(levelname)s %(message)s")
logging.getLogger("utils.ai").setLevel(
    logging.DEBUG if os.getenv("LOG_DEBUG") else logging.INFO
)

app = Client(
    "small_ai_bot",
    **PYROGRAM_CONFIG,
    plugins=dict(root="plugins"),
)

async def _main():
    from utils.config import LLM_CONFIG, LLM_VISION_MODE, LLM_VISION_CONFIG
    logging.warning(
        "LLM: url=%s model=%s vision=%s",
        LLM_CONFIG["url"], LLM_CONFIG["model"], LLM_VISION_MODE,
    )
    if LLM_VISION_MODE == "separate":
        logging.warning("Vision: url=%s model=%s", LLM_VISION_CONFIG["url"], LLM_VISION_CONFIG["model"])

    chats.init(CHATS_FILE)
    state.load_personas(PERSONAS_DIR)
    logging.warning("Personas loaded: %s", [k for k, _ in state.list_personas()])

    await app.start()
    me = await app.get_me()
    state.set_bot_name(me.first_name)
    logging.warning("Bot started as %s", me.first_name)

    await idle()
    await app.stop()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(_main())
