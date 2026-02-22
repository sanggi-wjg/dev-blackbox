from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dev_blackbox.storage.rds.entity.base import Base

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.user import User


class GitHubUserSecret(Base):
    __tablename__ = "github_user_secret"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    personal_access_token: Mapped[str] = mapped_column(String(255), nullable=False)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    user: Mapped["User"] = relationship("User", back_populates="github_user_secret")

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
