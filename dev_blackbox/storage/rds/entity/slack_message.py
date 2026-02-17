from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.storage.rds.entity.base import Base


class SlackMessage(Base):
    __tablename__ = "slack_message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    channel_id: Mapped[str] = mapped_column(String(100), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    message_ts: Mapped[str] = mapped_column(String(100), nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    message: Mapped[dict] = mapped_column(JSONB, nullable=False)
    thread_ts: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    slack_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("slack_user.id", ondelete="RESTRICT"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SlackMessage(channel_id={self.channel_id}, message_ts={self.message_ts})>"

    @classmethod
    def create(
        cls,
        user_id: int,
        slack_user_id: int,
        target_date: date,
        channel_id: str,
        channel_name: str,
        message_ts: str,
        message_text: str,
        message: dict,
        thread_ts: str | None = None,
    ) -> "SlackMessage":
        return cls(
            user_id=user_id,
            slack_user_id=slack_user_id,
            target_date=target_date,
            channel_id=channel_id,
            channel_name=channel_name,
            message_ts=message_ts,
            message_text=message_text,
            message=message,
            thread_ts=thread_ts,
        )
