from sqlalchemy import delete, select
from sqlalchemy.orm import Session

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

    def find_all_with_null_embedding(self) -> list[PlatformWorkLogChunk]:
        stmt = select(PlatformWorkLogChunk).where(
            PlatformWorkLogChunk.embedding.is_(None),
            PlatformWorkLogChunk.chunk_text != "",
        )
        return list(self.session.scalars(stmt))

    def find_similar_by_embedding(
        self,
        user_id: int,
        query_embedding: list[float],
        similarity: float,
        limit: int = 10,
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
