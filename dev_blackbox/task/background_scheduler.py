from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from dev_blackbox.task.collect_task import collect_platform_task
from dev_blackbox.task.default_task import health_task

scheduler = BackgroundScheduler(
    job_defaults={
        "misfire_grace_time": 3600,  # 1시간까지 지나도 실행 허요
        "max_instances": 1,  # 동일 작업 중복 실행 방지
        "coalesce": True,  # 밀린 실행 1회로 합침
    },
)
scheduler.configure(timezone="UTC")
scheduler.add_job(
    health_task,
    "interval",
    minutes=1,
)
scheduler.add_job(
    collect_platform_task,
    CronTrigger(hour=0, minute=0),
)
