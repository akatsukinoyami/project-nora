import yaml

_bot_name: str | None = None
_personas: dict = {}


def set_bot_name(name: str) -> None:
    global _bot_name
    _bot_name = name


def get_bot_name() -> str | None:
    return _bot_name


def load_personas(path: str) -> None:
    global _personas
    with open(path, "r", encoding="utf-8") as f:
        _personas = yaml.safe_load(f)


def _persona_entry(key: str) -> dict | str:
    return _personas.get(key) or _personas.get("default", "")


def get_system(persona_key: str) -> str:
    base = _personas.get("base_instructions", "")
    entry = _persona_entry(persona_key)
    system = entry.get("system", "") if isinstance(entry, dict) else entry
    return system + ("\n" + base if base else "")


def get_description(persona_key: str) -> str:
    entry = _persona_entry(persona_key)
    return entry.get("description", "") if isinstance(entry, dict) else ""


def list_personas() -> list[tuple[str, str]]:
    return [
        (k, v.get("description", "") if isinstance(v, dict) else "")
        for k, v in _personas.items()
        if k != "base_instructions"
    ]


def humanize(key: str) -> str:
    return " ".join(word.capitalize() for word in key.split("_"))
