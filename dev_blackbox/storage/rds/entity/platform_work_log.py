from datetime import date

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.base import Base


class PlatformWorkLog(Base):
    __tablename__ = "platform_work_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    platform: Mapped[PlatformEnum] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<PlatformWorkLog(user_id={self.user_id}, target_date={self.target_date}, platform={self.platform})>"

    @classmethod
    def create(
        cls,
        user_id: int,
        target_date: date,
        platform: PlatformEnum,
        content: str,
        model_name: str,
        prompt: str,
        embedding: list[float] | None = None,
    ) -> "PlatformWorkLog":
        return cls(
            user_id=user_id,
            target_date=target_date,
            platform=platform,
            content=content,
            model_name=model_name,
            prompt=prompt,
            embedding=embedding,
        )

    @property
    def markdown_text(self) -> str:
        return f"# {self.platform}\n\n{self.content}"

    def update_content(self, content: str) -> "PlatformWorkLog":
        self.content = content
        return self
