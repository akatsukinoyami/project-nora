# Small AI Bot

A small, fast Telegram bot powered by a local LLM via [Ollama](https://ollama.com). Responds with an anime character persona, handles text, photos, stickers, GIFs, and videos.

[Читать на русском](README.ru.md)

## Features

- Responds when mentioned, replied to, or always in private chats
- Reacts when addressed by name (e.g. "Aqua, what do you think?")
- Occasionally joins group conversations on its own (configurable chance)
- Handles photos, stickers, GIFs, and videos (frames extracted via OpenCV)
- Anime character personas defined in YAML — switch via env var
- Prompt injection detection — stays in character when someone tries to jailbreak it
- Typing indicator while generating a response

## Requirements

- Python 3.13 (3.14 breaks Pyrogram)
- [Ollama](https://ollama.com) running locally or on a remote host
- A vision-capable model, e.g. `gemma3:4b`

## Setup

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `BOT_TOKEN` | — | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `API_ID` | — | Telegram API ID from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | — | Telegram API hash |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama host URL |
| `OLLAMA_MODEL` | `gemma3:4b` | Model name |
| `PERSONAS_FILE` | `personas.yaml` | Path to personas file |
| `PERSONA_KEY` | `default` | Active persona key |

## Running

```bash
python app.py
```

## Personas

Personas are defined in `personas.yaml`. Each persona has a `system` key with the character description. A `base_instructions` block at the top is appended to every persona.

To add a persona, add a new key to the YAML and set `PERSONA_KEY` in `.env`.

## Project Structure

```
app.py              — bot entry point, handlers, filters
personas.yaml       — character personas
utils/
  config.py         — env vars (loads .env)
  ai.py             — Ollama client, injection detection, message building
  images.py         — image resize + base64 encode
  animations.py     — GIF/video frame extraction via OpenCV
```
