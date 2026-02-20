from datetime import date

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.storage.rds.entity.base import Base


class DailySummary(Base):
    __tablename__ = "daily_summary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<DailySummary(user_id={self.user_id}, target_date={self.target_date})>"

    @classmethod
    def create(
        cls,
        user_id: int,
        target_date: date,
        summary: str,
        embedding: list[float] | None = None,
    ) -> "DailySummary":
        return DailySummary(
            user_id=user_id,
            target_date=target_date,
            summary=summary,
            embedding=embedding,
        )
