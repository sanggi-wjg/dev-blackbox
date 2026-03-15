from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.projection.platform_work_log_projection import (
    PlatformWorkLogWithDistanceProjection,
)


class PlatformWorkLogRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, platform_work_log: PlatformWorkLog) -> PlatformWorkLog:
        self.session.add(platform_work_log)
        self.session.flush()
        return platform_work_log

    def find_all_by_id(self, ids: list[int]) -> list[PlatformWorkLog]:
        stmt = select(PlatformWorkLog).where(PlatformWorkLog.id.in_(ids))
        return list(self.session.scalars(stmt))

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
        self,
        user_id: int,
        target_date: date,
    ) -> list[PlatformWorkLog]:
        stmt = (
            select(PlatformWorkLog)
            .where(
                PlatformWorkLog.user_id == user_id,
                PlatformWorkLog.target_date == target_date,
            )
            .order_by(PlatformWorkLog.platform.asc())
        )
        return list(self.session.scalars(stmt))

    def find_by_id(self, platform_work_log_id: int) -> PlatformWorkLog | None:
        stmt = select(PlatformWorkLog).where(PlatformWorkLog.id == platform_work_log_id)
        return self.session.scalar(stmt)

    def find_all_with_null_embedding(self) -> list[PlatformWorkLog]:
        stmt = select(PlatformWorkLog).where(
            PlatformWorkLog.embedding.is_(None),
            PlatformWorkLog.is_empty.is_(False),
            PlatformWorkLog.content != "",
        )
        return list(self.session.scalars(stmt))

    def find_similar_by_embedding(
        self,
        user_id: int,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[PlatformWorkLogWithDistanceProjection]:
        distance = PlatformWorkLog.embedding.cosine_distance(query_embedding).label("distance")
        stmt = (
            select(PlatformWorkLog, distance)
            .where(
                PlatformWorkLog.user_id == user_id,
                PlatformWorkLog.embedding.is_not(None),
            )
            .order_by(distance.asc())
            .limit(limit)
        )
        results = self.session.execute(stmt).all()
        return [
            PlatformWorkLogWithDistanceProjection(platform_work_log=row[0], distance=row[1])
            for row in results
        ]

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
