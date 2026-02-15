from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dev_blackbox.storage.rds.entity.base import Base

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.user import User


class JiraUser(Base):
    __tablename__ = "jira_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    active: Mapped[bool] = mapped_column(default=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    user: Mapped["User"] = relationship("User", back_populates="jira_user")

    def __repr__(self) -> str:
        return f"<JiraUser(account_id={self.account_id}, display_name={self.display_name})>"

    @classmethod
    def create(
        cls,
        account_id: str,
        active: bool,
        display_name: str,
        email_address: str,
        url: str,
        user_id: int | None = None,
    ) -> "JiraUser":
        return cls(
            account_id=account_id,
            active=active,
            display_name=display_name,
            email_address=email_address,
            url=url,
            user_id=user_id,
        )

    def assign_user(self, user_id: int) -> "JiraUser":
        self.user_id = user_id
        return self
