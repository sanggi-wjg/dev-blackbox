from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dev_blackbox.storage.rds.entity.base import SoftDeleteMixin, Base

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.jira_user import JiraUser


class JiraSecret(SoftDeleteMixin, Base):
    __tablename__ = "jira_secret"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    api_token: Mapped[str] = mapped_column(String(512), nullable=False)

    jira_users: Mapped[list["JiraUser"]] = relationship("JiraUser", back_populates="jira_secret")

    def __repr__(self) -> str:
        return f"<JiraSecret(id={self.id}, name={self.name})>"

    @classmethod
    def create(
        cls,
        name: str,
        url: str,
        username: str,
        api_token: str,
    ) -> "JiraSecret":
        return cls(
            name=name,
            url=url,
            username=username,
            api_token=api_token,
        )
