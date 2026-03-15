import logging

from sqlalchemy.orm import Session

from dev_blackbox.service.command.embedding_command import UpdatePlatformWorkLogEmbeddingCommand
from dev_blackbox.storage.rds.repository import (
    DailyWorkLogRepository,
    PlatformWorkLogRepository,
)

logger = logging.getLogger(__name__)


class EmbeddingService:

    def __init__(self, session: Session):
        self.platform_work_log_repository = PlatformWorkLogRepository(session)
        self.daily_work_log_repository = DailyWorkLogRepository(session)

    def update_embedding(
        self,
        commands: list[UpdatePlatformWorkLogEmbeddingCommand],
    ) -> None:
        ids = [command.work_log_id for command in commands]
        command_map = {command.work_log_id: command.embedding for command in commands}
        work_logs = self.platform_work_log_repository.find_all_by_id(ids)

        for work_log in work_logs:
            work_log.update_embedding(command_map[work_log.id])
