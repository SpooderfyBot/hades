from typing import Dict, Any, Optional, Tuple
from asyncio import Future, get_event_loop, TimerHandle


class CacheObject:
    def __init__(self, internal: Any, ttl: Optional[float]):
        self._value = internal
        self._handle: Optional[TimerHandle] = None
        self._fut: Optional[Future] = None

        if ttl is not None:
            loop = get_event_loop()
            self._fut = loop.create_future()
            self._handle = loop.call_later(ttl, self._fut.set_result, None)

    def get_value(self) -> Tuple[bool, Any]:
        return self._fut.done(), self._value

    def clear(self):
        try:
            self._handle.cancel()
            self._fut.cancel()
        except:
            pass

    def __del__(self):
        self.clear()


class TTLCache:
    def __init__(self, ttl: Optional[float]):
        self._cache: Dict[Any, CacheObject] = {}
        self._ttl = ttl

    def set(self, key: Any, args: Any):
        self._cache[key] = CacheObject(args, ttl=self._ttl)

    def get(self, key: Any) -> Any:
        should_remove, value = self._cache[key].get_value()
        if should_remove:
            self._cache[key].clear()
            del self._cache[key]
            raise KeyError(f"Key {key!r} not in cache")
        return value


def ttl_cache(key_name: str, ttl: Optional[float] = None):
    cache = TTLCache(ttl)

    def wrapper(func):
        def wrap_cache(*args, **kwargs):
            key = kwargs[key_name]

            try:
                value = cache.get(key)
            except KeyError:
                value = func(*args, **kwargs)
                cache.set(key, value)
            return value
        return wrap_cache
    return wrapper


def async_ttl_cache(key_name: str, ttl: Optional[float] = None):
    cache = TTLCache(ttl)

    def wrapper(func):
        async def wrap_cache(*args, **kwargs):
            key = kwargs[key_name]

            try:
                value = cache.get(key)
            except KeyError:
                value = await func(*args, **kwargs)
                cache.set(key, value)
            return value

        return wrap_cache

    return wrapper
