from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dev_blackbox.storage.rds.entity.base import Base

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret
    from dev_blackbox.storage.rds.entity.user import User


class SlackUser(Base):
    __tablename__ = "slack_user"
    __table_args__ = (
        UniqueConstraint("slack_secret_id", "member_id", name="uq_slack_user_secret_member_id"),
        UniqueConstraint("user_id", name="uq_slack_user_user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, autoincrement=True)
    member_id: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    user: Mapped["User | None"] = relationship("User", back_populates="slack_user")

    slack_secret_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("slack_secret.id", ondelete="RESTRICT"),
        nullable=False,
    )
    slack_secret: Mapped["SlackSecret"] = relationship("SlackSecret", back_populates="slack_users")

    def __repr__(self) -> str:
        return f"<SlackUser(member_id={self.member_id}, display_name={self.display_name})>"

    @classmethod
    def create(
        cls,
        slack_secret_id: int,
        member_id: str,
        is_active: bool,
        display_name: str,
        real_name: str,
        email: str | None = None,
        user_id: int | None = None,
    ) -> "SlackUser":
        return cls(
            slack_secret_id=slack_secret_id,
            member_id=member_id,
            is_active=is_active,
            display_name=display_name,
            real_name=real_name,
            email=email,
            user_id=user_id,
        )

    def assign_user(self, user_id: int) -> "SlackUser":
        self.user_id = user_id
        return self

    def unassign_user(self) -> "SlackUser":
        self.user_id = None
        return self
