import json
import os

from pyrogram.types import Message

_path: str = "db.json"
_data: dict = {}


def init(path: str) -> None:
    global _path, _data
    _path = path
    os.makedirs(os.path.dirname(_path) or ".", exist_ok=True)
    if os.path.exists(_path):
        with open(_path, "r", encoding="utf-8") as f:
            _data = json.load(f)
    _data.setdefault("chats", {})
    _data.setdefault("users", {})


def _save() -> None:
    with open(_path, "w", encoding="utf-8") as f:
        json.dump(_data, f, ensure_ascii=False, indent=2)


def _chat(chat_id: int) -> dict:
    return _data["chats"].setdefault(str(chat_id), {})


def is_allowed(chat_id: int) -> bool:
    return _data["chats"].get(str(chat_id), {}).get("is_active", False)


def allow(chat_id: int) -> None:
    _chat(chat_id)["is_active"] = True
    _save()


def deny(chat_id: int) -> None:
    _chat(chat_id)["is_active"] = False
    _save()


def get_persona(chat_id: int) -> str | None:
    return _data["chats"].get(str(chat_id), {}).get("persona")


def set_persona(chat_id: int, persona: str) -> None:
    _chat(chat_id)["persona"] = persona
    _save()


def record_call(message: Message) -> None:
    if not message.from_user:
        return
    u = message.from_user
    chat = _chat(message.chat.id)

    c = message.chat
    chat["title"] = c.title or f"{c.first_name or ''} {c.last_name or ''}".strip() or str(c.id)
    if c.username:
        chat["username"] = c.username

    uid = str(u.id)
    chat.setdefault("calls", {})[uid] = chat.get("calls", {}).get(uid, 0) + 1

    user = _data["users"].setdefault(uid, {})
    if u.username:
        user["username"] = u.username
    user["name"] = f"{u.first_name or ''} {u.last_name or ''}".strip() or uid

    _save()
