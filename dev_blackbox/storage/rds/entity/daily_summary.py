from datetime import date

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.storage.rds.entity.base import Base


class DailySummary(Base):
    __tablename__ = "daily_summary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

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
        model_name: str,
        prompt: str,
        error_message: str | None = None,
        embedding: list[float] | None = None,
    ) -> "DailySummary":
        return cls(
            user_id=user_id,
            target_date=target_date,
            summary=summary,
            model_name=model_name,
            prompt=prompt,
            error_message=error_message,
            embedding=embedding,
        )
