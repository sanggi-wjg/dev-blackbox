from datetime import date

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.jira_event import JiraEvent


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
        for field, direction in (order_by or [("id", "asc")]):
            column = getattr(JiraEvent, field)
            stmt = stmt.order_by(column.asc() if direction == "asc" else column.desc())
        return list(self.session.scalars(stmt).all())

    def delete_by_user_id_and_target_date(self, user_id: int, target_date: date) -> None:
        stmt = delete(JiraEvent).where(
            JiraEvent.user_id == user_id,
            JiraEvent.target_date == target_date,
        )
        self.session.execute(stmt)
        self.session.flush()
