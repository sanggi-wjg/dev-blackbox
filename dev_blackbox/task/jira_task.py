import logging

from dev_blackbox.core.database import get_db_session
from dev_blackbox.core.enum import DistributedLockName
from dev_blackbox.service.jira_user_service import JiraUserService
from dev_blackbox.util.distributed_lock import distributed_lock

logger = logging.getLogger(__name__)


def sync_jira_users_task():
    with distributed_lock(DistributedLockName.SYNC_JIRA_USERS_TASK) as acquired:
        if not acquired:
            logger.warning("sync_jira_users_task is already running, skipping...")
            return

        logger.info("sync_jira_users_task started...")

        with get_db_session() as session:
            JiraUserService(session).sync_all_jira_users()

        logger.info("sync_jira_users_task completed.")
