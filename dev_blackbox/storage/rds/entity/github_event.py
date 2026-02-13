from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.client.model.github_model import GithubCommitModel, GithubEventModel
from dev_blackbox.storage.rds.entity.base import Base


class GitHubEvent(Base):
    __tablename__ = 'github_event'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    event: Mapped[dict] = mapped_column(JSONB, nullable=False)
    commit: Mapped[dict] = mapped_column(JSONB, nullable=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
    )
    github_user_secret_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('github_user_secret.id', ondelete='RESTRICT'),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f'<GitHubEvent(event_id={self.event_id}, user_id={self.user_id})>'

    @classmethod
    def create(
        cls,
        user_id: int,
        github_user_secret_id: int,
        target_date: date,
        event: GithubEventModel,
        commit: GithubCommitModel | None,
    ) -> "GitHubEvent":
        return cls(
            user_id=user_id,
            github_user_secret_id=github_user_secret_id,
            target_date=target_date,
            event_id=event.id,
            event=event.model_dump(mode='json'),
            commit=commit.model_dump(mode='json') if commit else None,
        )

    def get_event(self) -> GithubEventModel:
        return GithubEventModel.model_validate(self.event)

    def get_commit(self) -> GithubCommitModel:
        return GithubCommitModel.model_validate(self.commit)
