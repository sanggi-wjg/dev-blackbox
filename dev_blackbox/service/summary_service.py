import logging
from datetime import date

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.daily_summary import DailySummary
from dev_blackbox.storage.rds.entity.platform_summary import PlatformSummary
from dev_blackbox.storage.rds.repository import PlatformSummaryRepository, DailySummaryRepository

logger = logging.getLogger(__name__)


class SummaryService:

    def __init__(self, session: Session):
        self.session = session
        self.platform_summary_repository = PlatformSummaryRepository(session)
        self.daily_summary_repository = DailySummaryRepository(session)

    def save_platform_summary(
        self,
        user_id: int,
        target_date: date,
        platform: PlatformEnum,
        summary: str,
        model_name: str,
        prompt: str,
        embedding: list[float] | None = None,
    ) -> PlatformSummary:
        """
        기존 요약 삭제 후 새로 저장
        """
        self.platform_summary_repository.delete_by_user_id_and_target_date_and_platform(
            user_id=user_id, target_date=target_date, platform=platform
        )
        platform_summary = PlatformSummary.create(
            user_id=user_id,
            target_date=target_date,
            platform=platform,
            summary=summary,
            model_name=model_name,
            prompt=prompt,
            embedding=embedding,
        )
        return self.platform_summary_repository.save(platform_summary)

    def get_platform_summaries(self, user_id: int, target_date: date) -> list[PlatformSummary]:
        return self.platform_summary_repository.find_all_by_user_id_and_target_date(
            user_id, target_date
        )

    def save_daily_summary(
        self,
        user_id: int,
        target_date: date,
    ) -> DailySummary:
        platform_summaries = self.get_platform_summaries(user_id, target_date)
        summary_text = "\n\n".join(summary.markdown_text for summary in platform_summaries)

        # 기존 일일 요약 삭제 후 새로 저장
        self.daily_summary_repository.delete_by_user_id_and_target_date(
            user_id=user_id, target_date=target_date
        )
        daily_summary = DailySummary.create(
            user_id=user_id,
            target_date=target_date,
            summary=summary_text,
        )
        return self.daily_summary_repository.save(daily_summary)

    def get_daily_summary(self, user_id: int, target_date: date) -> DailySummary | None:
        return self.daily_summary_repository.find_by_user_id_and_target_date(user_id, target_date)

    def get_all_daily_summaries(self, user_id: int) -> list[DailySummary]:
        return self.daily_summary_repository.find_all_by_user_id(user_id)
