# Small AI Bot

Маленький быстрый Telegram-бот на базе локальной LLM через [Ollama](https://ollama.com). Отвечает с характером аниме-персонажа, обрабатывает текст, фото, стикеры, GIF и видео.

[Read in English](README.md)

## Возможности

- Отвечает при упоминании, ответе на его сообщение или всегда в личных чатах
- Реагирует на обращение по имени (например: "Аква, что думаешь?")
- Иногда сам вмешивается в разговор в группе (настраиваемый шанс)
- Обрабатывает фото, стикеры, GIF и видео (кадры извлекаются через OpenCV)
- Персонажи описаны в YAML — переключение через переменную окружения
- Защита от prompt injection — остаётся в роли при попытке взлома
- Показывает индикатор набора текста во время генерации ответа

## Требования

- Python 3.13 (3.14 ломает Pyrogram)
- [Ollama](https://ollama.com) локально или на удалённом хосте
- Модель с поддержкой изображений, например `gemma3:4b`

## Установка

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

## Конфигурация

| Переменная | По умолчанию | Описание |
|---|---|---|
| `BOT_TOKEN` | — | Токен бота от [@BotFather](https://t.me/BotFather) |
| `API_ID` | — | Telegram API ID с [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | — | Telegram API hash |
| `OLLAMA_URL` | `http://localhost:11434` | Адрес Ollama |
| `OLLAMA_MODEL` | `gemma3:4b` | Название модели |
| `PERSONAS_FILE` | `personas.yaml` | Путь к файлу персон |
| `PERSONA_KEY` | `default` | Активная персона |

## Запуск

```bash
python app.py
```

## Персоны

Персоны описаны в `personas.yaml`. У каждой персоны есть ключ `system` с описанием характера. Блок `base_instructions` в начале файла добавляется к каждой персоне.

Чтобы добавить персону — добавьте новый ключ в YAML и задайте `PERSONA_KEY` в `.env`.

## Структура проекта

```
app.py              — точка входа, хендлеры, фильтры
personas.yaml       — персонажи
utils/
  config.py         — переменные окружения (загружает .env)
  ai.py             — клиент Ollama, защита от инъекций, формирование сообщений
  images.py         — ресайз изображений + base64
  animations.py     — извлечение кадров из GIF/видео через OpenCV
```
