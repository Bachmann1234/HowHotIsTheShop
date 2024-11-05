import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CacheEntry:
    data: str
    epoc_timeout: Optional[float]


_cache: Dict[str, CacheEntry] = {}


def get_cache_value(key: str) -> Optional[str]:
    value = _cache.get(key)
    if not value or (value.epoc_timeout and value.epoc_timeout < int(time.time())):
        return None
    return value.data


def set_cache_value(key: str, data: str, timeout_epoc: Optional[float] = None):
    _cache[key] = CacheEntry(data, timeout_epoc)


def clear_cache():
    _cache.clear()


def clear_cache_entry(key: str):
    del _cache[key]
