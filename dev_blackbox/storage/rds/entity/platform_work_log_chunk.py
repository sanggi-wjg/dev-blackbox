from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.storage.rds.entity.base import Base


class PlatformWorkLogChunk(Base):
    __tablename__ = "platform_work_log_chunk"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    platform_work_log_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("platform_work_log.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)

    def __repr__(self) -> str:
        return f"<PlatformWorkLogChunk(id={self.id}, platform_work_log_id={self.platform_work_log_id}, chunk_index={self.chunk_index})>"

    @classmethod
    def create(
        cls,
        platform_work_log_id: int,
        chunk_index: int,
        chunk_text: str,
        embedding: list[float] | None = None,
    ) -> "PlatformWorkLogChunk":
        return cls(
            platform_work_log_id=platform_work_log_id,
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            embedding=embedding,
        )
