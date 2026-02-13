from typing import TYPE_CHECKING, List
from zoneinfo import ZoneInfo

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dev_blackbox.storage.rds.entity.base import SoftDeleteMixin, Base

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.github_user_secret import GitHubUserSecret


class User(SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="사용자 이름")
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="이메일")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Seoul")

    github_user_secrets: Mapped[List["GitHubUserSecret"]] = relationship(
        "GitHubUserSecret",
        back_populates="user",
        order_by="GitHubUserSecret.id",
    )

    def __repr__(self) -> str:
        return f"<User(name={self.name}, email={self.email})>"

    @classmethod
    def create(cls, name: str, email: str) -> "User":
        return cls(name=name, email=email)

    @property
    def tz_info(self):
        return ZoneInfo(self.timezone)
