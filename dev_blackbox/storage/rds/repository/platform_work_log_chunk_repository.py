from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.platform_work_log_chunk import PlatformWorkLogChunk
from dev_blackbox.storage.rds.projection.projections import (
    PlatformWorkLogChunkWithDistanceProjection,
)


class PlatformWorkLogChunkRepository:

    def __init__(self, session: Session):
        self.session = session

    def save_all(self, chunks: list[PlatformWorkLogChunk]) -> list[PlatformWorkLogChunk]:
        self.session.add_all(chunks)
        self.session.flush()
        return chunks

    def find_all_by_ids(self, ids: list[int]) -> list[PlatformWorkLogChunk]:
        stmt = select(PlatformWorkLogChunk).where(PlatformWorkLogChunk.id.in_(ids))
        return list(self.session.scalars(stmt))

    def find_similar_by_embedding(
        self,
        user_id: int,
        query_embedding: list[float],
        similarity: float,
        limit: int = 10,
        platform: PlatformEnum | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[PlatformWorkLogChunkWithDistanceProjection]:
        distance = PlatformWorkLogChunk.embedding.cosine_distance(query_embedding).label("distance")
        stmt = (
            select(PlatformWorkLogChunk, distance)
            .join(
                PlatformWorkLog,
                PlatformWorkLogChunk.platform_work_log_id == PlatformWorkLog.id,
            )
            .where(
                PlatformWorkLog.user_id == user_id,
                PlatformWorkLogChunk.embedding.is_not(None),
                distance < (1.0 - similarity),
            )
            .order_by(distance.asc())
            .limit(limit)
        )

        if platform is not None:
            stmt = stmt.where(PlatformWorkLog.platform == platform)
        if from_date is not None:
            stmt = stmt.where(PlatformWorkLog.target_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(PlatformWorkLog.target_date <= to_date)

        results = self.session.execute(stmt).all()
        return [
            PlatformWorkLogChunkWithDistanceProjection(
                platform_work_log_chunk=row[0], distance=row[1]
            )
            for row in results
        ]

    def delete_by_platform_work_log_ids(self, ids: list[int]) -> None:
        if not ids:
            return
        stmt = delete(PlatformWorkLogChunk).where(
            PlatformWorkLogChunk.platform_work_log_id.in_(ids)
        )
        self.session.execute(stmt)
        self.session.flush()
