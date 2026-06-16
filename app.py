import asyncio
import logging

from pyrogram import Client, idle

from utils import state
from utils.chats import Chats
from utils.config import API_ID, API_HASH, BOTS, PERSONAS_DIR, PERSONA_KEY


logging.basicConfig(level=logging.WARNING, format="%(name)s %(levelname)s %(message)s")


def _make_client(name: str, cfg: dict) -> Client:
    client = Client(
        name,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=cfg["token"],
        workdir="data",
        plugins=dict(root="plugins"),
    )
    client.chats = Chats(f"data/{name}.json")
    client.default_persona = cfg.get("persona", PERSONA_KEY)
    client.bot_name = None
    client.debug_vision = False
    return client


async def _start(client: Client) -> None:
    await client.start()
    me = await client.get_me()
    client.bot_name = me.first_name
    logging.warning("Bot started: name=%s session=%s", me.first_name, client.name)


async def _main():
    from utils.config import LLM_CONFIG, LLM_VISION_MODE, LLM_VISION_CONFIG
    logging.warning(
        "LLM: url=%s model=%s vision=%s",
        LLM_CONFIG["url"], LLM_CONFIG["model"], LLM_VISION_MODE,
    )
    if LLM_VISION_MODE == "separate":
        logging.warning("Vision: url=%s model=%s", LLM_VISION_CONFIG["url"], LLM_VISION_CONFIG["model"])

    state.load_personas(PERSONAS_DIR)
    logging.warning("Personas loaded: %s", [k for k, _ in state.list_personas()])

    clients = [_make_client(name, cfg) for name, cfg in BOTS.items()]
    await asyncio.gather(*[_start(c) for c in clients])

    await idle()

    await asyncio.gather(*[c.stop() for c in clients])


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(_main())
