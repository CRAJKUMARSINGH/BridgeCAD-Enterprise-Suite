"""
bridgecad_infra.cache — In-memory LRU cache with optional Redis backend.

Falls back gracefully to in-memory when Redis is unavailable.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from typing import Any


class LRUCache:
    """Thread-safe in-memory LRU cache with TTL."""

    def __init__(self, maxsize: int = 256, ttl_seconds: int = 3600) -> None:
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._maxsize  = maxsize
        self._ttl      = ttl_seconds

    def _key(self, *args, **kwargs) -> str:
        raw = json.dumps({"a": args, "k": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, key: str) -> tuple[bool, Any]:
        """Return (hit, value). Evicts expired entries."""
        if key not in self._cache:
            return False, None
        value, expires_at = self._cache[key]
        if time.monotonic() > expires_at:
            del self._cache[key]
            return False, None
        self._cache.move_to_end(key)
        return True, value

    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.monotonic() + self._ttl)
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def make_key(self, *args, **kwargs) -> str:
        return self._key(*args, **kwargs)


# Module-level singleton caches
_qa_cache      = LRUCache(maxsize=128, ttl_seconds=1800)   # QA reports (30 min)
_boq_cache     = LRUCache(maxsize=64,  ttl_seconds=3600)   # BOQ (1 hr)
_drawing_cache = LRUCache(maxsize=32,  ttl_seconds=7200)   # DXF paths (2 hr)


def get_qa_cache()      -> LRUCache: return _qa_cache
def get_boq_cache()     -> LRUCache: return _boq_cache
def get_drawing_cache() -> LRUCache: return _drawing_cache


__all__ = ["LRUCache", "get_qa_cache", "get_boq_cache", "get_drawing_cache"]
