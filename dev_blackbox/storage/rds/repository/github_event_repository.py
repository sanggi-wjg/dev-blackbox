from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.github_event import GitHubEvent


class GitHubEventRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, github_event: GitHubEvent) -> GitHubEvent:
        self.session.add(github_event)
        self.session.flush()
        return github_event

    def save_all(self, github_events: list[GitHubEvent]) -> list[GitHubEvent]:
        self.session.add_all(github_events)
        self.session.flush()
        return github_events

    def delete_all(self, github_events: list[GitHubEvent]) -> None:
        for event in github_events:
            self.session.delete(event)
        self.session.flush()

    def find_all_by_user_id(self, user_id: int) -> list[GitHubEvent]:
        stmt = (
            select(GitHubEvent)
            .where(GitHubEvent.user_id == user_id)
            .order_by(GitHubEvent.target_date.asc())
        )
        return list(self.session.scalars(stmt).all())

    def find_all_by_user_id_and_target_date(
        self, user_id: int, target_date: date
    ) -> list[GitHubEvent]:
        stmt = (
            select(GitHubEvent)
            .where(
                GitHubEvent.user_id == user_id,
                GitHubEvent.target_date == target_date,
            )
            .order_by(GitHubEvent.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def exists_by_event_id(self, event_id: str) -> bool:
        stmt = select(GitHubEvent.id).where(GitHubEvent.event_id == event_id)
        return self.session.scalar(stmt) is not None
