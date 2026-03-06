import logging

from dev_blackbox.core.const import LockKey
from dev_blackbox.core.database import get_db_session
from dev_blackbox.service.jira_user_service import JiraUserService
from dev_blackbox.util.distributed_lock import distributed_lock

logger = logging.getLogger(__name__)


def sync_jira_users_task():
    with distributed_lock(LockKey.SYNC_JIRA_USERS_TASK) as acquired:
        if not acquired:
            logger.warning("Jira 사용자 동기화 태스크가 이미 실행 중, 건너뜀...")
            return

        logger.info("Jira 사용자 동기화 태스크 시작...")

        with get_db_session() as session:
            JiraUserService(session).sync_all_jira_users()

        logger.info("Jira 사용자 동기화 태스크 완료.")
