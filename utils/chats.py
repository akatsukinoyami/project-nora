import json
import os

from pyrogram.types import Message


class Chats:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = {}
        self._data.setdefault("chats", {})
        self._data.setdefault("users", {})

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _chat(self, chat_id: int) -> dict:
        return self._data["chats"].setdefault(str(chat_id), {})

    def is_allowed(self, chat_id: int) -> bool:
        return self._data["chats"].get(str(chat_id), {}).get("is_active", False)

    def allow(self, chat_id: int) -> None:
        self._chat(chat_id)["is_active"] = True
        self._save()

    def deny(self, chat_id: int) -> None:
        self._chat(chat_id)["is_active"] = False
        self._save()

    def get_persona(self, chat_id: int) -> str | None:
        return self._data["chats"].get(str(chat_id), {}).get("persona")

    def set_persona(self, chat_id: int, persona: str) -> None:
        self._chat(chat_id)["persona"] = persona
        self._save()

    def record_call(self, message: Message) -> None:
        if not message.from_user:
            return
        u = message.from_user
        chat = self._chat(message.chat.id)

        c = message.chat
        chat["title"] = c.title or f"{c.first_name or ''} {c.last_name or ''}".strip() or str(c.id)
        if c.username:
            chat["username"] = c.username

        uid = str(u.id)
        chat.setdefault("calls", {})[uid] = chat.get("calls", {}).get(uid, 0) + 1

        user = self._data["users"].setdefault(uid, {})
        if u.username:
            user["username"] = u.username
        user["name"] = f"{u.first_name or ''} {u.last_name or ''}".strip() or uid

        self._save()
