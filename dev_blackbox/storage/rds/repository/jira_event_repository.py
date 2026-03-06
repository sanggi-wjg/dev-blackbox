from datetime import date

from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.jira_event import JiraEvent
from dev_blackbox.storage.rds.projection.projections import EventCountByDateProjection


class JiraEventRepository:

    def __init__(self, session: Session):
        self.session = session

    def save_all(self, jira_events: list[JiraEvent]) -> list[JiraEvent]:
        self.session.add_all(jira_events)
        self.session.flush()
        return jira_events

    def find_all_by_user_id_and_target_date(
        self,
        user_id: int,
        target_date: date,
        order_by: list[tuple[str, str]] | None = None,
    ) -> list[JiraEvent]:
        stmt = select(JiraEvent).where(
            JiraEvent.user_id == user_id,
            JiraEvent.target_date == target_date,
        )
        for field, direction in order_by or [("id", "asc")]:
            column = getattr(JiraEvent, field)
            stmt = stmt.order_by(column.asc() if direction == "asc" else column.desc())
        return list(self.session.scalars(stmt))

    def count_by_user_id_and_dates_group_by_date(
        self,
        user_id: int,
        from_date: date,
        to_date: date,
    ) -> list[EventCountByDateProjection]:
        stmt = (
            select(JiraEvent.target_date, func.count())
            .where(
                JiraEvent.user_id == user_id,
                JiraEvent.target_date.between(from_date, to_date),
            )
            .group_by(JiraEvent.target_date)
            .order_by(JiraEvent.target_date.asc())
        )
        result = list(self.session.execute(stmt).tuples())
        return [EventCountByDateProjection(*r) for r in result]

    def delete_by_user_id_and_target_date(self, user_id: int, target_date: date) -> None:
        stmt = delete(JiraEvent).where(
            JiraEvent.user_id == user_id,
            JiraEvent.target_date == target_date,
        )
        self.session.execute(stmt)
        self.session.flush()
