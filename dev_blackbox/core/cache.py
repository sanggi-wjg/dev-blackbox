from functools import lru_cache

import redis
from redis import Redis, RedisError

from dev_blackbox.core.config import get_settings

"""
https://github.com/redis/redis-py
"""


@lru_cache(maxsize=10)
def get_redis_client(database: int) -> Redis | None:
    _redis_secret = get_settings().redis
    try:
        return redis.Redis(
            host=_redis_secret.host,
            port=_redis_secret.port,
            db=database,
        )
    except RedisError:
        return None
