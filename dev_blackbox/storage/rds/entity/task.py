from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.core.enum import TaskStatusEnum
from dev_blackbox.storage.rds.entity.base import Base
from dev_blackbox.util.datetime_util import get_datetime_utc_now


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[TaskStatusEnum] = mapped_column(String(50), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"

    @classmethod
    def create(
        cls,
        user_id: int,
        title: str,
        status: TaskStatusEnum,
        content: str = "",
        tags: str | None = None,
        display_order: int = 0,
    ) -> "Task":
        return cls(
            user_id=user_id,
            title=title,
            content=content,
            tags=tags,
            status=status,
            display_order=display_order,
        )

    def update(
        self,
        title: str,
        content: str,
        tags: str | None,
        status: TaskStatusEnum,
        display_order: int,
    ) -> "Task":
        self.title = title
        self.content = content
        self.tags = tags
        self.status = status
        self.display_order = display_order
        return self

    def archive(self) -> "Task":
        self.is_archived = True
        self.archived_at = get_datetime_utc_now()
        return self

    def unarchive(self) -> "Task":
        self.is_archived = False
        return self
