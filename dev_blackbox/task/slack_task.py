import logging

from dev_blackbox.core.database import get_db_session
from dev_blackbox.service.slack_user_service import SlackUserService
from dev_blackbox.util.distributed_lock import DistributedLockName, distributed_lock

logger = logging.getLogger(__name__)


def sync_slack_users_task():
    with distributed_lock(DistributedLockName.SYNC_SLACK_USERS_TASK) as acquired:
        if not acquired:
            logger.warning("sync_slack_users_task is already running, skipping...")
            return

        logger.info("sync_slack_users_task started...")

        with get_db_session() as session:
            service = SlackUserService(session)
            service.sync_slack_users()

        logger.info("sync_slack_users_task completed.")
