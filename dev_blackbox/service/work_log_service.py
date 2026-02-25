import logging
from datetime import date

from sqlalchemy.orm import Session

from dev_blackbox.core.cache import cache_evict, cacheable
from dev_blackbox.core.const import CacheKey
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.repository import PlatformWorkLogRepository, DailyWorkLogRepository

logger = logging.getLogger(__name__)


class WorkLogService:

    def __init__(self, session: Session):
        self.session = session
        self.platform_work_log_repository = PlatformWorkLogRepository(session)
        self.daily_work_log_repository = DailyWorkLogRepository(session)

    def save_platform_work_log(
        self,
        user_id: int,
        target_date: date,
        platform: PlatformEnum,
        content: str,
        model_name: str,
        prompt: str,
        embedding: list[float] | None = None,
    ) -> PlatformWorkLog:
        # 기존 요약 삭제 후 새로 저장
        self.platform_work_log_repository.delete_by_user_id_and_target_date_and_platform(
            user_id=user_id,
            target_date=target_date,
            platform=platform,
        )
        platform_work_log = PlatformWorkLog.create(
            user_id=user_id,
            target_date=target_date,
            platform=platform,
            content=content,
            model_name=model_name,
            prompt=prompt,
            embedding=embedding,
        )
        return self.platform_work_log_repository.save(platform_work_log)

    @cacheable(key=CacheKey.WORK_LOG_PLATFORM)
    def get_platform_work_logs(
        self,
        user_id: int,
        target_date: date,
        platforms: list[PlatformEnum],
    ) -> list[PlatformWorkLog]:
        return self.platform_work_log_repository.find_all_by_user_id_and_target_date_and_platforms(
            user_id,
            target_date,
            platforms,
        )

    def save_daily_work_log(
        self,
        user_id: int,
        target_date: date,
    ) -> DailyWorkLog:
        # user_content 제외
        platform_work_logs = (
            self.platform_work_log_repository.find_all_by_user_id_and_target_date_and_platforms(
                user_id,
                target_date,
                PlatformEnum.platforms(),
            )
        )
        merged_work_log_text = "\n\n".join(
            work_log.markdown_text for work_log in platform_work_logs
        )

        # 기존 일일 요약 삭제 후 새로 저장
        self.daily_work_log_repository.delete_by_user_id_and_target_date(
            user_id=user_id, target_date=target_date
        )
        daily_work_log = DailyWorkLog.create(
            user_id=user_id,
            target_date=target_date,
            content=merged_work_log_text,
        )
        return self.daily_work_log_repository.save(daily_work_log)

    def get_daily_work_log(
        self,
        user_id: int,
        target_date: date,
    ) -> DailyWorkLog | None:
        return self.daily_work_log_repository.find_by_user_id_and_target_date(user_id, target_date)

    def get_daily_work_logs(self, user_id: int) -> list[DailyWorkLog]:
        return self.daily_work_log_repository.find_all_by_user_id(user_id)

    @cacheable(key=CacheKey.WORK_LOG_USER_CONTENT)
    def get_user_content_or_none(self, user_id: int, target_date: date) -> PlatformWorkLog | None:
        return self.platform_work_log_repository.find_by_user_id_and_target_date_and_platform(
            user_id=user_id,
            target_date=target_date,
            platform=PlatformEnum.USER_CONTENT,
        )

    @cache_evict(key=CacheKey.WORK_LOG_USER_CONTENT)
    def create_or_update_user_content(
        self,
        user_id: int,
        target_date: date,
        content: str,
    ) -> tuple[bool, PlatformWorkLog]:
        work_log = self.platform_work_log_repository.find_by_user_id_and_target_date_and_platform(
            user_id=user_id,
            target_date=target_date,
            platform=PlatformEnum.USER_CONTENT,
        )
        if work_log is None:
            platform_work_log = PlatformWorkLog.create(
                user_id=user_id,
                target_date=target_date,
                platform=PlatformEnum.USER_CONTENT,
                content=content,
                model_name="",
                prompt="",
            )
            return True, self.platform_work_log_repository.save(platform_work_log)
        else:
            return False, work_log.update_content(content)
