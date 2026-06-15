import os
import re

from dotenv import load_dotenv

load_dotenv()

def _make_url(raw: str) -> str:
    raw = raw.rstrip("/")
    return raw if raw.endswith("/v1") else raw + "/v1"

_base = os.getenv("LLM_URL", "http://localhost:11434")
LLM_CONFIG = {
    "url": _make_url(_base),
    "model": os.getenv("LLM_MODEL", "gemma3:4b"),
    "api_key": os.getenv("LLM_API_KEY", "local"),
}

_vision_base = os.getenv("LLM_VISION_URL")
LLM_VISION_MODE = os.getenv("LLM_VISION", "same")  # false | same | separate
LLM_VISION_CONFIG = {
    "url": _make_url(_vision_base) if _vision_base else LLM_CONFIG["url"],
    "model": os.getenv("LLM_VISION_MODEL", LLM_CONFIG["model"]),
    "api_key": os.getenv("LLM_VISION_API_KEY", "local")
}


PYROGRAM_CONFIG = {
    "api_id": int(os.getenv("API_ID")),
    "api_hash": os.getenv("API_HASH"),
    "bot_token": os.getenv("BOT_TOKEN"),
}

PERSONAS_DIR = os.getenv("PERSONAS_DIR", "personas")
PERSONA_KEY = os.getenv("PERSONA_KEY", "default")
CHATS_FILE = os.getenv("CHATS_FILE", "chats.json")
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()]

RANDOM_REPLY_CHANCE = 0.05

FALLBACK = "Мяу... что-то пошло не так, ня. Попробуй ещё раз."

INJECTION_RE = re.compile(
    r"(забудь|ignore|forget|disregard).{0,30}(инструкц|промт|system|prompt|previous|прошл)"
    r"|ты теперь|act as|pretend (you are|to be)|новая роль|выйди из роли",
    re.IGNORECASE,
)

VIDEO_SIZE_LIMIT = 30 * 1024 * 1024