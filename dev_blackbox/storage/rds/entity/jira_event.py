from datetime import date
from functools import cached_property

from sqlalchemy import BigInteger, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.client.model.jira_api_model import JiraIssueModel
from dev_blackbox.storage.rds.entity.base import Base


class JiraEvent(Base):
    __tablename__ = "jira_event"
    __table_args__ = ()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    issue_id: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_key: Mapped[str] = mapped_column(String(100), nullable=False)
    issue: Mapped[dict] = mapped_column(JSONB, nullable=False)
    changelog: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    jira_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("jira_user.id", ondelete="RESTRICT"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<JiraEvent(issue_key={self.issue_key}, user_id={self.user_id})>"

    @classmethod
    def create(
        cls,
        user_id: int,
        jira_user_id: int,
        target_date: date,
        issue_id: str,
        issue_key: str,
        issue: dict,
        changelog: list | None,
    ) -> "JiraEvent":
        return cls(
            user_id=user_id,
            jira_user_id=jira_user_id,
            target_date=target_date,
            issue_id=issue_id,
            issue_key=issue_key,
            issue=issue,
            changelog=changelog,
        )

    @cached_property
    def issue_model(self) -> JiraIssueModel:
        return JiraIssueModel.model_validate(self.issue)
