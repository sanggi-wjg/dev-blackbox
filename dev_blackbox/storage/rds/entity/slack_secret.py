from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dev_blackbox.storage.rds.entity.base import SoftDeleteMixin, Base

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.slack_user import SlackUser


class SlackSecret(SoftDeleteMixin, Base):
    __tablename__ = "slack_secret"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bot_token: Mapped[str] = mapped_column(String(512), nullable=False)

    slack_users: Mapped[list["SlackUser"]] = relationship(
        "SlackUser", back_populates="slack_secret"
    )

    def __repr__(self) -> str:
        return f"<SlackSecret(id={self.id}, name={self.name})>"

    @classmethod
    def create(
        cls,
        name: str,
        bot_token: str,
    ) -> "SlackSecret":
        return cls(
            name=name,
            bot_token=bot_token,
        )
