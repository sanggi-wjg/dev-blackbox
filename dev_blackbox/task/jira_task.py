import logging

from dev_blackbox.core.database import get_db_session
from dev_blackbox.service.jira_user_service import JiraUserService
from dev_blackbox.util.distributed_lock import DistributedLockName
from dev_blackbox.util.distributed_lock import distributed_lock

logger = logging.getLogger(__name__)


def sync_jira_users_task():
    with distributed_lock(DistributedLockName.SYNC_JIRA_USERS_TASK) as acquired:
        if not acquired:
            logger.warning("sync_jira_users_task is already running, skipping...")
            return

        with get_db_session() as session:
            service = JiraUserService(session)
            service.sync_jira_users()
