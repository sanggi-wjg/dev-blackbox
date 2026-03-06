from datetime import date

from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.slack_message import SlackMessage
from dev_blackbox.storage.rds.projection.projections import EventCountByDateProjection


class SlackMessageRepository:

    def __init__(self, session: Session):
        self.session = session

    def save_all(self, slack_messages: list[SlackMessage]) -> list[SlackMessage]:
        self.session.add_all(slack_messages)
        self.session.flush()
        return slack_messages

    def find_all_by_user_id_and_target_date(
        self,
        user_id: int,
        target_date: date,
        order_by: list[tuple[str, str]] | None = None,
    ) -> list[SlackMessage]:
        stmt = select(SlackMessage).where(
            SlackMessage.user_id == user_id,
            SlackMessage.target_date == target_date,
        )
        for field, direction in order_by or [("id", "asc")]:
            column = getattr(SlackMessage, field)
            stmt = stmt.order_by(column.asc() if direction == "asc" else column.desc())
        return list(self.session.scalars(stmt))

    def count_by_user_id_and_dates_group_by_date(
        self,
        user_id: int,
        from_date: date,
        to_date: date,
    ) -> list[EventCountByDateProjection]:
        stmt = (
            select(SlackMessage.target_date, func.count())
            .where(
                SlackMessage.user_id == user_id,
                SlackMessage.target_date.between(from_date, to_date),
            )
            .group_by(SlackMessage.target_date)
            .order_by(SlackMessage.target_date.asc())
        )
        result = list(self.session.execute(stmt).tuples())
        return [EventCountByDateProjection(*r) for r in result]

    def delete_by_user_id_and_target_date(self, user_id: int, target_date: date) -> None:
        stmt = delete(SlackMessage).where(
            SlackMessage.user_id == user_id,
            SlackMessage.target_date == target_date,
        )
        self.session.execute(stmt)
        self.session.flush()
