import os
import re

from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_URL", "http://localhost:11434").removesuffix("/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

PERSONAS_FILE = os.getenv("PERSONAS_FILE", "personas.yaml")
PERSONA_KEY = os.getenv("PERSONA_KEY", "default")

RANDOM_REPLY_CHANCE = 0.05


FALLBACK = "Мяу... что-то пошло не так, ня. Попробуй ещё раз."

INJECTION_RE = re.compile(
    r"(забудь|ignore|forget|disregard).{0,30}(инструкц|промт|system|prompt|previous|прошл)"
    r"|ты теперь|act as|pretend (you are|to be)|новая роль|выйди из роли",
    re.IGNORECASE,
)

VIDEO_SIZE_LIMIT = 30 * 1024 * 1024