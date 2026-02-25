import functools
import inspect
import logging
import pickle
from functools import lru_cache
from typing import Any, Callable

import redis
from redis import Redis
from redis.lock import Lock

from dev_blackbox.core.config import get_settings
from dev_blackbox.core.const import DEFAULT_CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=10)
def get_redis_client(database: int = 0) -> Redis:
    """
    https://github.com/redis/redis-py
    """
    _redis_secret = get_settings().redis
    return redis.Redis(
        host=_redis_secret.host,
        port=_redis_secret.port,
        db=database,
        encoding="UTF-8",
        socket_timeout=10,
        socket_connect_timeout=10,
    )


class CacheService:

    def __init__(
        self,
        cache_client: Redis | None = None,
    ):
        self.cache_client = cache_client or get_redis_client()

    def get(self, key: str) -> Any | None:
        data: bytes | None = self.cache_client.get(key)  # pyright: ignore [reportAssignmentType]
        if data is None:
            return None
        return pickle.loads(data)

    def exists(self, key: str) -> bool:
        return bool(self.cache_client.exists(key))

    def set(
        self,
        key: str,
        value: Any,
        nx: bool = False,
        ex: int = DEFAULT_CACHE_TTL_SECONDS,
    ):
        return self.cache_client.set(
            key,
            pickle.dumps(value),
            nx=nx,
            ex=ex,
        )

    def delete(self, key: str):
        return self.cache_client.delete(key)


class LockService:

    def __init__(
        self,
        cache_client: Redis | None = None,
    ):
        self.cache_client = cache_client or get_redis_client()

    def lock(
        self,
        key: str,
        timeout: int,
        blocking_timeout: int,
    ) -> Lock:
        return self.cache_client.lock(
            f"lock:{key}",
            timeout,
            blocking_timeout,
        )


def resolve_cache_key(key_template: str, func: Callable, *args, **kwargs) -> str:
    """
    key_template = "iam_function:text:{text}:args:{args}:kwargs:{kwargs}"
    key = resolve_cache_key(key_template, iam_function, "test", 1, 2, a=3, b=4)
    assert key == "iam_function:text:test:args:(1, 2):kwargs:{'a': 3, 'b': 4}"
    """
    sign = inspect.signature(func)
    bound = sign.bind(*args, **kwargs)
    bound.apply_defaults()
    return key_template.format(**bound.arguments)


def cacheable(key: str, ttl: int = DEFAULT_CACHE_TTL_SECONDS):
    """
    @cacheable(key='user:{user_id}', ttl=300)
    def get_user(user_id: int) -> dict:
        ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_service = CacheService()
            cache_key = resolve_cache_key(key, func, *args, **kwargs)

            if cache_service.exists(cache_key):
                return cache_service.get(cache_key)

            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ex=ttl)
            return result

        return wrapper

    return decorator


def cache_put(key: str, ttl: int = DEFAULT_CACHE_TTL_SECONDS):
    """
    @cache_put(key='user:{user_id}', ttl=300)
    def update_user(user_id: int, name: str) -> dict:
        ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            cache_key = resolve_cache_key(key, func, *args, **kwargs)

            cache_service = CacheService()
            cache_service.set(cache_key, result, ex=ttl)
            return result

        return wrapper

    return decorator


def cache_evict(key: str):
    """
    @cache_evict(key='user:{user_id}')
    def delete_user(user_id: int) -> None:
        ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            cache_key = resolve_cache_key(key, func, *args, **kwargs)

            cache_service = CacheService()
            cache_service.delete(cache_key)
            return result

        return wrapper

    return decorator
