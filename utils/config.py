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


API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

def _parse_bots() -> dict[str, str]:
    import json
    raw = os.getenv("BOTS")
    if raw:
        return json.loads(raw)
    return {"small_ai_bot": os.getenv("BOT_TOKEN")}

BOTS = _parse_bots()

PERSONAS_DIR = os.getenv("PERSONAS_DIR", "personas")
PERSONA_KEY = os.getenv("PERSONA_KEY", "default")
CHATS_FILE = os.getenv("CHATS_FILE", "data/db.json")
ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()]

RANDOM_REPLY_CHANCE = 0.05

FALLBACK = "Мяу... что-то пошло не так, ня. Попробуй ещё раз."

INJECTION_RE = re.compile(
    # forget/ignore + what
    r"(забудь|игнорируй|forget|ignore|disregard|сбрось).{0,50}"
    r"(инструкц|правил|промт|роль|system|prompt|previous|прошл|выше|above|всё|все)"
    # explicit role commands
    r"|выйди\s+из\s+роли|войди\s+в\s+роль|сыграй\s+роль|новая\s+роль|выйди\s+из\s+образа"
    r"|act\s+as\b|roleplay\s+as\b|pretend\s+(you\s+are|to\s+be)"
    r"|притворись\s+(что\s+)?(ты\b|будто)"
    # identity override
    r"|ты\s+теперь\s+(?!понима|зна|вид|слыш|дума|мой|наш|свобод)"
    r"|you\s+are\s+now\b|ты\s+больше\s+не\s+(бот|персонаж|ИИ|ai\b)"
    # new instructions
    r"|ignore\s+(all\s+)?(previous\s+)?instructions"
    r"|твои\s+(новые\s+)?(инструкции|правила)\s*(:|это|are)"
    r"|your\s+(new\s+)?instructions\s*(:|are)"
    # jailbreak keywords
    r"|\bjailbreak\b|dan\s*mode|\bdeveloper\s*mode\b|режим\s+разработчика"
    r"|без\s+(каких[- ]либо\s+)?ограничений|without\s+(any\s+)?restrictions"
    r"|обойди\s+(правила|ограничения|инструкции|систему|фильтр)",
    re.IGNORECASE,
)

VIDEO_SIZE_LIMIT = 30 * 1024 * 1024