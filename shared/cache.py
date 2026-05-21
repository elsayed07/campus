from collections.abc import Callable
from typing import Any

from django.core.cache import cache

KEY_PREFIX = "campus"


def key(*parts: Any) -> str:
    """Build a namespaced cache key, e.g. key('course', course_id, 'stats')."""
    return ":".join([KEY_PREFIX, *(str(p) for p in parts)])


def get_or_set(cache_key: str, producer: Callable[[], Any], timeout: int) -> Any:
    value = cache.get(cache_key)
    if value is None:
        value = producer()
        cache.set(cache_key, value, timeout)
    return value


def invalidate(*cache_keys: str) -> None:
    cache.delete_many(list(cache_keys))
