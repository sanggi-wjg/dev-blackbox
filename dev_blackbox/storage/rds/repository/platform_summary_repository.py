from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.platform_summary import PlatformSummary


class PlatformSummaryRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, platform_summary: PlatformSummary) -> PlatformSummary:
        self.session.add(platform_summary)
        self.session.flush()
        return platform_summary

    def find_by_user_id_and_target_date_and_platform(
        self, user_id: int, target_date: date, platform: PlatformEnum
    ) -> PlatformSummary | None:
        stmt = select(PlatformSummary).where(
            PlatformSummary.user_id == user_id,
            PlatformSummary.target_date == target_date,
            PlatformSummary.platform == platform,
        )
        return self.session.scalar(stmt)

    def find_all_by_user_id_and_target_date(
        self, user_id: int, target_date: date
    ) -> list[PlatformSummary]:
        stmt = (
            select(PlatformSummary)
            .where(
                PlatformSummary.user_id == user_id,
                PlatformSummary.target_date == target_date,
            )
            .order_by(PlatformSummary.platform.asc())
        )
        return list(self.session.scalars(stmt).all())

    def delete_by_user_id_and_target_date_and_platform(
        self,
        user_id: int,
        target_date: date,
        platform: PlatformEnum,
    ) -> None:
        stmt = delete(PlatformSummary).where(
            PlatformSummary.user_id == user_id,
            PlatformSummary.target_date == target_date,
            PlatformSummary.platform == platform,
        )
        self.session.execute(stmt)
        self.session.flush()
