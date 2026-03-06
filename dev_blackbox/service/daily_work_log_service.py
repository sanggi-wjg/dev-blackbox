from sqlalchemy.orm import Session

from dev_blackbox.service.command.daily_work_log_command import SaveDailyWorkLogCommand
from dev_blackbox.service.query.daily_work_log_query import DailyWorkLogQuery
from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog
from dev_blackbox.storage.rds.repository import (
    DailyWorkLogRepository,
    PlatformWorkLogRepository,
)


class DailyWorkLogService:

    def __init__(self, session: Session):
        self.daily_work_log_repository = DailyWorkLogRepository(session)
        self.platform_work_log_repository = PlatformWorkLogRepository(session)

    def get_daily_work_log(self, query: DailyWorkLogQuery) -> DailyWorkLog | None:
        return self.daily_work_log_repository.find_by_user_id_and_target_date(
            query.user_id, query.target_date
        )

    def save_daily_work_log(self, command: SaveDailyWorkLogCommand) -> DailyWorkLog:
        # 기존 일일 요약 삭제 후 새로 저장
        self.daily_work_log_repository.delete_by_user_id_and_target_date(
            user_id=command.user_id,
            target_date=command.target_date,
        )

        platform_work_logs = self.platform_work_log_repository.find_all_by_user_id_and_target_date(
            user_id=command.user_id,
            target_date=command.target_date,
        )
        merged_work_log_text = "\n\n".join(
            work_log.markdown_text for work_log in platform_work_logs
        )
        if not merged_work_log_text:
            merged_work_log_text = ""

        daily_work_log = DailyWorkLog.create(
            user_id=command.user_id,
            target_date=command.target_date,
            content=merged_work_log_text,
        )
        return self.daily_work_log_repository.save(daily_work_log)
