from datetime import datetime, UTC
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dev_blackbox.storage.rds.entity.base import Base, SoftDeleteMixin

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.user import User


class GitHubUserSecret(SoftDeleteMixin, Base):
    __tablename__ = "github_user_secret"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    personal_access_token: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    deactivate_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user: Mapped["User"] = relationship("User", back_populates="github_user_secrets")

    def __repr__(self) -> str:
        return f"<GitHubUserSecret(username={self.username}, user_id={self.user_id})>"

    @classmethod
    def create(
        cls,
        username: str,
        personal_access_token: str,
        user_id: int,
    ) -> "GitHubUserSecret":
        return cls(
            username=username,
            personal_access_token=personal_access_token,
            user_id=user_id,
        )

    def deactivate(self):
        self.is_active = False
        self.deactivate_at = datetime.now(UTC)
