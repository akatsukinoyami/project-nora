import asyncio
import json
import os
from typing import Callable, Awaitable

_path: str = "data/media_cache.json"
_data: dict[str, str] = {}
_inflight: dict[str, asyncio.Future] = {}


def init(path: str = "data/media_cache.json") -> None:
    global _path, _data
    _path = path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _data = json.load(f)


def _save() -> None:
    tmp = _path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_data, f, ensure_ascii=False)
    os.replace(tmp, _path)


def get(key: str) -> str | None:
    return _data.get(key)


async def get_or_compute(
    key: str,
    compute: Callable[[], Awaitable[str]],
) -> str:
    # Fast path — cache hit (atomic, no await before this check)
    if key in _data:
        return _data[key]

    # Another coroutine is already computing this key — wait for it
    if key in _inflight:
        return await asyncio.shield(_inflight[key])

    # We're first — register a Future so others can wait on us
    fut: asyncio.Future = asyncio.get_event_loop().create_future()
    _inflight[key] = fut

    try:
        result = await compute()
        if result:
            _data[key] = result
            _save()
        fut.set_result(result)
        return result
    except Exception as e:
        fut.set_exception(e)
        raise
    finally:
        _inflight.pop(key, None)