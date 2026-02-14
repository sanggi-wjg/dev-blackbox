from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from dev_blackbox.core.database import engine
from dev_blackbox.task.collect_task import collect_platform_task
from dev_blackbox.task.health_task import health_check_task

"""
https://apscheduler.readthedocs.io/en/3.x/userguide.html#
"""


class _BackgroundSchedulerStores:
    DEFAULT = "default"
    REDIS = "redis"


class _BackgroundSchedulerExecutors:
    DEFAULT = "default"
    PROCESS_POOL = "processpool"


scheduler = BackgroundScheduler(
    stores={
        _BackgroundSchedulerStores.DEFAULT: SQLAlchemyJobStore(engine=engine),
        # _BackgroundSchedulerStores.REDIS: RedisJobStore(host='localhost', port=6379),
    },
    executors={
        _BackgroundSchedulerExecutors.DEFAULT: ThreadPoolExecutor(20),
        _BackgroundSchedulerExecutors.PROCESS_POOL: ProcessPoolExecutor(5),
    },
    job_defaults={
        "misfire_grace_time": 3600,  # 1시간까지 지나도 실행 허요
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
