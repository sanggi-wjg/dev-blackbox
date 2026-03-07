from datetime import date

from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.github_event import GitHubEvent
from dev_blackbox.storage.rds.projection.projections import EventCountByDateProjection


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

    def find_all_by_user_id(self, user_id: int) -> list[GitHubEvent]:
        stmt = (
            select(GitHubEvent)
            .where(GitHubEvent.user_id == user_id)
            .order_by(GitHubEvent.target_date.asc(), GitHubEvent.id.asc())
        )
        return list(self.session.scalars(stmt))

    def find_all_by_user_id_and_target_date(
        self,
        user_id: int,
        target_date: date,
        order_by: list[tuple[str, str]] | None = None,
    ) -> list[GitHubEvent]:
        stmt = select(GitHubEvent).where(
            GitHubEvent.user_id == user_id,
            GitHubEvent.target_date == target_date,
        )
        for field, direction in order_by or [("id", "asc")]:
            column = getattr(GitHubEvent, field)
            stmt = stmt.order_by(column.asc() if direction == "asc" else column.desc())
        return list(self.session.scalars(stmt))

    def count_by_user_id_and_dates_group_by_date(
        self,
        user_id: int,
        from_date: date,
        to_date: date,
    ) -> list[EventCountByDateProjection]:
        stmt = (
            select(GitHubEvent.target_date, func.count())
            .where(
                GitHubEvent.user_id == user_id,
                GitHubEvent.target_date.between(from_date, to_date),
            )
            .group_by(GitHubEvent.target_date)
            .order_by(GitHubEvent.target_date.asc())
        )
        result = list(self.session.execute(stmt).tuples())
        return [EventCountByDateProjection(*r) for r in result]

    def delete_by_user_id_and_target_date(self, user_id: int, target_date: date) -> None:
        stmt = delete(GitHubEvent).where(
            GitHubEvent.user_id == user_id,
            GitHubEvent.target_date == target_date,
        )
        self.session.execute(stmt)
        self.session.flush()

    def find_all_by_user_id_and_target_date_and_event_types(
        self,
        user_id: int,
        target_date: date,
        event_types: list[str],
    ) -> list[GitHubEvent]:
        stmt = (
            select(GitHubEvent)
            .where(
                GitHubEvent.user_id == user_id,
                GitHubEvent.target_date == target_date,
                GitHubEvent.event_type.in_(event_types),
            )
            .order_by(GitHubEvent.id.asc())
        )
        return list(self.session.scalars(stmt))
