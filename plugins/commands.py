import functools
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message

from utils import chats, state
from utils.ai import ask_text
from utils.config import ALLOWED_USERS, PERSONA_KEY


def _is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id in ALLOWED_USERS)


def _system(chat_id: int) -> str:
    return state.get_system(chats.get_persona(chat_id) or PERSONA_KEY)


def _persona_key(chat_id: int) -> str:
    return chats.get_persona(chat_id) or PERSONA_KEY


async def _reply_in_character(client: Client, message: Message, situation: str):
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    text = await ask_text(situation, _system(message.chat.id))
    await message.reply(text)


def admin(func):
    @functools.wraps(func)
    async def wrapper(client: Client, message: Message):
        if not _is_admin(message):
            await _reply_in_character(
                client, message,
                "Кто-то без прав попытался использовать команду администратора. Откажи ему с юмором — что-то вроде 'ты даже не гражданин'. Коротко."
            )
            return
        return await func(client, message)
    return wrapper


@Client.on_message(filters.command("ping"))
async def on_ping(client: Client, message: Message):
    await _reply_in_character(client, message, "Пользователь проверяет, живой ли ты. Ответь очень коротко.")


@Client.on_message(filters.command("allow"))
@admin
async def on_allow(client: Client, message: Message):
    chats.allow(message.chat.id)
    await _reply_in_character(client, message, "Администратор только что добавил этот чат в разрешённые — теперь ты можешь здесь общаться. Отреагируй коротко.")


@Client.on_message(filters.command("deny"))
@admin
async def on_deny(client: Client, message: Message):
    chats.deny(message.chat.id)
    await _reply_in_character(client, message, "Администратор только что убрал этот чат из разрешённых — ты больше не будешь здесь отвечать. Попрощайся коротко.")


@Client.on_message(filters.command("persona"))
async def on_persona(client: Client, message: Message):
    key = _persona_key(message.chat.id)
    name = state.get_name(key)
    description = state.get_description(key)
    await _reply_in_character(
        client, message,
        f"Представься одной фразой: 'Я — {name}, {description}' — и добавь что-то от себя в своём стиле. Очень коротко."
    )


@Client.on_message(filters.command("personas"))
async def on_personas(_: Client, message: Message):
    lines = [f"• {state.get_name(k)} — {desc}" for k, desc in state.list_personas()]
    await message.reply("\n".join(lines))


@Client.on_message(filters.command("chats") & filters.private)
@admin
async def on_chats(client: Client, message: Message):
    from utils.config import CHATS_FILE
    await client.send_document(message.chat.id, CHATS_FILE, reply_to_message_id=message.id)


@Client.on_message(filters.command("persona_set"))
@admin
async def on_persona_set(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Использование: /persona_set <ключ>")
        return

    key = state.resolve_key(args[1].strip())
    if key is None:
        available = [state.get_name(k) for k, _ in state.list_personas()]
        await message.reply(f"Персона не найдена.\nДоступные: {', '.join(available)}")
        return

    chats.set_persona(message.chat.id, key)
    new_system = state.get_system(key)
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    text = await ask_text(f"Тебя только что переключили на персону {state.get_name(key)}. Представься коротко.", new_system)
    await message.reply(text)
