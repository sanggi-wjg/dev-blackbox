from datetime import datetime, UTC

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.storage.rds.entity.base import Base, SoftDeleteMixin


class GitHubUserSecret(SoftDeleteMixin, Base):
    __tablename__ = "github_user_secret"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    personal_access_token: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    deactivate_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    def __repr__(self) -> str:
        return f"<GitHubUserSecret(username={self.username})>"

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
