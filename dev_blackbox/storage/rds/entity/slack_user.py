from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dev_blackbox.storage.rds.entity.base import Base

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.user import User


class SlackUser(Base):
    __tablename__ = "slack_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, autoincrement=True)
    member_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )
    user: Mapped["User | None"] = relationship("User", back_populates="slack_user")

    def __repr__(self) -> str:
        return f"<SlackUser(member_id={self.member_id}, display_name={self.display_name})>"

    @classmethod
    def create(
        cls,
        member_id: str,
        display_name: str,
        real_name: str,
        email: str | None = None,
        user_id: int | None = None,
    ) -> "SlackUser":
        return cls(
            member_id=member_id,
            display_name=display_name,
            real_name=real_name,
            email=email,
            user_id=user_id,
        )

    def assign_user(self, user_id: int) -> "SlackUser":
        self.user_id = user_id
        return self
