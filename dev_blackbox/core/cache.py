from enum import Enum
from functools import lru_cache

import redis
from redis import Redis

from dev_blackbox.core.config import get_settings

"""
https://github.com/redis/redis-py
"""


@lru_cache(maxsize=10)
def get_redis_client(database: int = 0) -> Redis:
    _redis_secret = get_settings().redis
    return redis.Redis(
        host=_redis_secret.host,
        port=_redis_secret.port,
        db=database,
        encoding="utf-8",
    )


class DistributedLockName(str, Enum):
    SYNC_JIRA_USERS_TASK = "sync_jira_users_task"
    SYNC_SLACK_USERS_TASK = "sync_slack_users_task"
    COLLECT_EVENTS_AND_SUMMARIZE_WORK_LOG_TASK = "collect_events_and_summarize_work_log_task"
