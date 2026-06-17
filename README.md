# Project Nora

[English](#english) | [Русский](#русский)

---

## English

A small Telegram bot powered by a local LLM via [Ollama](https://ollama.com) or any OpenAI-compatible API (DeepSeek, mlx_lm, etc.). Responds with an anime character persona, handles text, photos, stickers, GIFs, and videos.

### Features

- Responds when mentioned, replied to, or always in private chats
- Reacts when addressed by name (e.g. "Aqua, what do you think?")
- Occasionally joins group conversations on its own (configurable chance)
- Handles photos, stickers, GIFs, and videos (frames extracted via OpenCV)
- Media groups (albums) processed as a single message — each file described separately, text model infers context across them
- Vision descriptions cached by `file_unique_id` in `data/media_cache.json` — repeated files skip download and vision entirely
- Anime character personas defined in individual YAML files — switch per chat via bot command
- Three vision modes:
  - `same` - images sent to main LLM
  - `separate` - local vision model describes, text sent to main LLM
  - `false` - ignore images
- Two-layer prompt injection protection
  - regex pre-filter catches common patterns
  - system prompt instructs the persona to stay in character regardless
- Per-chat persona switching and allow/deny control
- Typing indicator while generating a response

> **Note:** Response quality depends heavily on the model you use. Small local models will stay in character but may feel generic; larger or instruction-tuned models produce much more expressive results.

### Requirements

- Python 3.13 (3.14 breaks Pyrogram)
- [Ollama](https://ollama.com) running locally or any OpenAI-compatible backend
- A model that fits your hardware, e.g. `gemma3:4b`

### Setup

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Running Ollama

```bash
ollama serve
ollama pull gemma3:4b
python app.py
```

### Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `BOT_TOKEN` | — | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `API_ID` | — | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | — | Telegram API hash |
| `ALLOWED_USERS` | — | Comma-separated Telegram user IDs with admin access |
| `LLM_URL` | `http://localhost:11434` | LLM backend URL |
| `LLM_MODEL` | `gemma3:4b` | Model name |
| `LLM_API_KEY` | `local` | API key (use any string for local backends) |
| `LLM_VISION` | `same` | Vision mode: `same`, `separate`, or `false` |
| `LLM_VISION_URL` | `LLM_URL` | Vision model backend URL (for `separate` mode) |
| `LLM_VISION_MODEL` | `LLM_MODEL` | Vision model name |
| `LLM_VISION_API_KEY` | `local` | Vision model API key |
| `PERSONAS_DIR` | `personas` | Path to personas directory |
| `PERSONA_KEY` | `default` | Default persona key (filename without `.yaml`) |
| `CHATS_FILE` | `db.json` | Path to database file |

### Commands

For BotFather (`/setcommands`):

```text
ping - check if the bot is alive
allow - enable the bot in this chat (admin)
deny - disable the bot in this chat (admin)
persona - show current persona
personas - list all available personas
persona_set - set persona for this chat (admin)
chats - download db.json (admin, private only)
id - show chat id, user id, and file_unique_id(s) with cached vision description
reload_cache - reload media_cache.json from disk (admin, private only)
```

### Personas

Personas live in the `personas/` directory as individual YAML files:

```yaml
name: Aqua                  # string or {ru: "Аква", en: "Aqua"}
description: Short description shown in /personas
prompt: |
  You are Aqua from KonoSuba...
```

`_base.yaml` is special — its `prompt` is appended to every persona.

To add a persona, create a new `.yaml` file in `personas/`. Switch with `/persona_set <name>` — any name variant works (`Аква`, `Aqua`, `aqua`).

### Project Structure

```text
app.py              — entry point
personas/           — persona YAML files
data/
  {name}.json       — per-bot chat state (allow/deny, persona, stats)
  {name}.session    — Pyrogram session file
  media_cache.json  — shared vision description cache (file_unique_id → description)
utils/
  config.py         — env vars
  ai.py             — LLM client, vision, injection detection
  state.py          — persona loading and lookup
  chats.py          — per-chat state (allow/deny, persona, stats)
  media_cache.py    — shared vision cache with race-condition-safe get_or_compute
  animations.py     — GIF/video frame extraction via OpenCV
plugins/
  reply.py          — message handlers (single messages and media groups)
  commands.py       — bot commands
```

---

## Русский

Маленький Telegram-бот на базе локальной LLM через [Ollama](https://ollama.com) или любого OpenAI-совместимого API (DeepSeek, mlx_lm и др.). Отвечает с характером аниме-персонажа, обрабатывает текст, фото, стикеры, GIF и видео.

### Возможности

- Отвечает при упоминании, ответе на его сообщение или всегда в личных чатах
- Реагирует на обращение по имени (например: "Аква, что думаешь?")
- Иногда сам вмешивается в разговор в группе (настраиваемый шанс)
- Обрабатывает фото, стикеры, GIF и видео (кадры извлекаются через OpenCV)
- Медиагруппы (альбомы) обрабатываются как одно сообщение — каждый файл описывается отдельно, текстовая модель сама находит связь между ними
- Описания от vision-модели кешируются по `file_unique_id` в `data/media_cache.json` — повторные файлы пропускают скачивание и vision полностью
- Персонажи описаны в отдельных YAML-файлах — переключение для каждого чата через команду
- Три режима работы с изображениями:
  - `same` - картинки идут в основную LLM
  - `separate` - локальная vision-модель описывает, текст идёт в основную LLM
  - `false` - игнорировать медиа
- Двухуровневая защита от prompt injection:
  - regex-фильтр отлавливает типичные паттерны
  - системный промт инструктирует персону оставаться в роли в любом случае
- Настройка персоны и доступа отдельно для каждого чата
- Показывает индикатор набора текста во время генерации ответа

> **Примечание:** Качество ответов очень сильно зависит от используемой модели. Маленькие локальные модели будут держать персону, но могут быть безликими; большие или instruction-tuned модели дают заметно более живые результаты.

### Требования

- Python 3.13 (3.14 ломает Pyrogram)
- [Ollama](https://ollama.com) локально или любой OpenAI-совместимый бекенд
- Модель под ваше железо, например `gemma3:4b`

### Установка

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Запуск через Ollama

```bash
ollama serve
ollama pull gemma3:4b
python app.py
```

### Конфигурация

| Переменная | По умолчанию | Описание |
| --- | --- | --- |
| `BOT_TOKEN` | — | Токен бота от [@BotFather](https://t.me/BotFather) |
| `API_ID` | — | Telegram API ID с [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | — | Telegram API hash |
| `ALLOWED_USERS` | — | ID пользователей Telegram с правами администратора через запятую |
| `LLM_URL` | `http://localhost:11434` | Адрес LLM бекенда |
| `LLM_MODEL` | `gemma3:4b` | Название модели |
| `LLM_API_KEY` | `local` | API-ключ (любая строка для локальных бекендов) |
| `LLM_VISION` | `same` | Режим работы с изображениями: `same`, `separate` или `false` |
| `LLM_VISION_URL` | `LLM_URL` | Адрес vision-модели (для режима `separate`) |
| `LLM_VISION_MODEL` | `LLM_MODEL` | Название vision-модели |
| `LLM_VISION_API_KEY` | `local` | API-ключ vision-модели |
| `PERSONAS_DIR` | `personas` | Путь к директории с персонами |
| `PERSONA_KEY` | `default` | Персона по умолчанию (имя файла без `.yaml`) |
| `CHATS_FILE` | `db.json` | Путь к файлу базы данных |

### Команды

Для BotFather (`/setcommands`):

```text
ping - проверить, живой ли бот
allow - разрешить боту отвечать в этом чате (админ)
deny - запретить боту отвечать в этом чате (админ)
persona - показать текущую персону
personas - список всех доступных персон
persona_set - сменить персону для этого чата (админ)
chats - скачать db.json (админ, только в личке)
id - показать id чата, пользователя и file_unique_id(s) с кешированным описанием
reload_cache - перезагрузить media_cache.json с диска (админ, только в личке)
```

### Персоны

Персоны хранятся в директории `personas/` как отдельные YAML-файлы:

```yaml
name: Аква                  # строка или {ru: "Аква", en: "Aqua"}
description: Короткое описание для /personas
prompt: |
  Ты — Аква из KonoSuba...
```

`_base.yaml` — особый файл: его `prompt` добавляется к каждой персоне.

Чтобы добавить персону — создайте новый `.yaml` файл в `personas/`. Переключение через `/persona_set <имя>` — работает любой вариант имени (`Аква`, `Aqua`, `aqua`).

### Структура проекта

```text
app.py              — точка входа
personas/           — YAML-файлы персон
data/
  {name}.json       — состояние чатов каждого бота (доступ, персона, статистика)
  {name}.session    — сессия Pyrogram
  media_cache.json  — общий кеш vision-описаний (file_unique_id → описание)
utils/
  config.py         — переменные окружения
  ai.py             — LLM-клиент, vision, защита от инъекций
  state.py          — загрузка и поиск персон
  chats.py          — состояние чатов (доступ, персона, статистика)
  media_cache.py    — общий кеш vision с защитой от race condition
  animations.py     — извлечение кадров из GIF/видео через OpenCV
plugins/
  reply.py          — обработчики сообщений (одиночные и медиагруппы)
  commands.py       — команды бота
```
