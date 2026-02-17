from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from dev_blackbox.core.config import get_settings
from dev_blackbox.task.collect_task import collect_platform_task
from dev_blackbox.task.health_task import health_check_task
from dev_blackbox.task.jira_task import sync_jira_users_task
from dev_blackbox.task.slack_task import sync_slack_users_task

"""
https://apscheduler.readthedocs.io/en/3.x/userguide.html#
"""

_redis_secret = get_settings().redis


class _BackgroundSchedulerStores:
    DEFAULT = "default"


class _BackgroundSchedulerExecutors:
    DEFAULT = "default"
    PROCESS_POOL = "processpool"


scheduler = BackgroundScheduler(
    stores={
        _BackgroundSchedulerStores.DEFAULT: RedisJobStore(
            host=_redis_secret.host,
            port=_redis_secret.port,
        ),
    },
    executors={
        _BackgroundSchedulerExecutors.DEFAULT: ThreadPoolExecutor(20),
        _BackgroundSchedulerExecutors.PROCESS_POOL: ProcessPoolExecutor(5),
    },
    job_defaults={
        "misfire_grace_time": 3600,  # 1시간까지 지나도 실행 허용
        "max_instances": 1,  # 동일 작업 중복 실행 방지
        "coalesce": False,
    },
    timezone="UTC",
)

scheduler.add_job(health_check_task, "interval", minutes=1)
scheduler.add_job(
    collect_platform_task,
    CronTrigger(hour=0, minute=0),
)
scheduler.add_job(
    sync_jira_users_task,
    CronTrigger(hour=15, minute=00),
)
scheduler.add_job(
    sync_slack_users_task,
    CronTrigger(hour=15, minute=30),
)
