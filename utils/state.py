import glob
import os

import yaml

_bot_name: str | None = None
_personas: dict[str, dict] = {}
_base: str = ""
_name_index: dict[str, str] = {}  # lowercased name variant → persona key


def set_bot_name(name: str) -> None:
    global _bot_name
    _bot_name = name


def get_bot_name() -> str | None:
    return _bot_name


def load_personas(directory: str) -> None:
    global _personas, _base, _name_index
    _personas = {}
    _base = ""
    _name_index = {}

    for path in sorted(glob.glob(os.path.join(directory, "*.yaml"))):
        key = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if key == "_base":
            _base = data.get("prompt", "")
        else:
            _personas[key] = data
            _name_index[key.lower()] = key
            name = data.get("name")
            if isinstance(name, str):
                _name_index[name.lower()] = key
            elif isinstance(name, dict):
                for v in name.values():
                    if isinstance(v, str):
                        _name_index[v.lower()] = key


def _prompt_for(entry: dict, lang: str) -> str:
    prompt = entry.get("prompt", "")
    if isinstance(prompt, dict):
        return prompt.get(lang) or next(iter(prompt.values()), "")
    return prompt


def get_system(persona_key: str, lang: str = "ru") -> str:
    entry = _personas.get(persona_key) or _personas.get("default", {})
    prompt = _prompt_for(entry, lang)
    return prompt + ("\n" + _base if _base else "")


def resolve_key(input: str) -> str | None:
    return _name_index.get(input.strip().lower())


def get_name(persona_key: str, lang: str = "ru") -> str:
    name = _personas.get(persona_key, {}).get("name")
    if isinstance(name, dict):
        return name.get(lang) or next(iter(name.values()), humanize(persona_key))
    return name or humanize(persona_key)


def get_description(persona_key: str) -> str:
    return _personas.get(persona_key, {}).get("description", "")


def list_personas() -> list[tuple[str, str]]:
    return [(k, v.get("description", "")) for k, v in _personas.items()]


def humanize(key: str) -> str:
    return " ".join(word.capitalize() for word in key.split("_"))
