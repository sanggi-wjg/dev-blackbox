import logging

from dev_blackbox.core.const import LockKey
from dev_blackbox.core.database import get_db_session
from dev_blackbox.service.slack_user_service import SlackUserService
from dev_blackbox.util.distributed_lock import distributed_lock

logger = logging.getLogger(__name__)


def sync_slack_users_task():
    with distributed_lock(LockKey.SYNC_SLACK_USERS_TASK) as acquired:
        if not acquired:
            logger.warning("Slack 사용자 동기화 태스크가 이미 실행 중, 건너뜀...")
            return

        logger.info("Slack 사용자 동기화 태스크 시작...")

        with get_db_session() as session:
            service = SlackUserService(session)
            service.sync_all_slack_users()

        logger.info("Slack 사용자 동기화 태스크 완료.")
