import time
from dataclasses import dataclass


@dataclass
class CacheEntry:
    data: str
    epoc_timeout: float | None


_cache: dict[str, CacheEntry] = {}


def get_cache_value(key: str) -> str | None:
    value = _cache.get(key)
    if not value or (value.epoc_timeout and value.epoc_timeout < int(time.time())):
        return None
    return value.data


def set_cache_value(key: str, data: str, timeout_epoc: float | None = None):
    _cache[key] = CacheEntry(data, timeout_epoc)


def clear_cache_entry(key: str):
    del _cache[key]
