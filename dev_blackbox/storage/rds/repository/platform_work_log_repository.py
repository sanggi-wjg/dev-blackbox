from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog


class PlatformWorkLogRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, platform_work_log: PlatformWorkLog) -> PlatformWorkLog:
        self.session.add(platform_work_log)
        self.session.flush()
        return platform_work_log

    def find_by_user_id_and_target_date_and_platform(
        self, user_id: int, target_date: date, platform: PlatformEnum
    ) -> PlatformWorkLog | None:
        stmt = select(PlatformWorkLog).where(
            PlatformWorkLog.user_id == user_id,
            PlatformWorkLog.target_date == target_date,
            PlatformWorkLog.platform == platform,
        )
        return self.session.scalar(stmt)

    def find_all_by_user_id_and_target_date(
        self, user_id: int, target_date: date
    ) -> list[PlatformWorkLog]:
        stmt = (
            select(PlatformWorkLog)
            .where(
                PlatformWorkLog.user_id == user_id,
                PlatformWorkLog.target_date == target_date,
            )
            .order_by(PlatformWorkLog.platform.asc())
        )
        return list(self.session.scalars(stmt).all())

    def delete_by_user_id_and_target_date_and_platform(
        self,
        user_id: int,
        target_date: date,
        platform: PlatformEnum,
    ) -> None:
        stmt = delete(PlatformWorkLog).where(
            PlatformWorkLog.user_id == user_id,
            PlatformWorkLog.target_date == target_date,
            PlatformWorkLog.platform == platform,
        )
        self.session.execute(stmt)
        self.session.flush()
