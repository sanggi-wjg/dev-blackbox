from datetime import datetime, timezone

from sqlalchemy import func, DateTime, text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

NOT_DELETED = datetime(9999, 12, 31, 14, 59, 59, tzinfo=timezone.utc)


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("'9999-12-31 14:59:59+00'"),
        default=NOT_DELETED,
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(default=False)

    def delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
