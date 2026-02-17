from datetime import date

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.slack_message import SlackMessage


class SlackMessageRepository:

    def __init__(self, session: Session):
        self.session = session

    def save_all(self, slack_messages: list[SlackMessage]) -> list[SlackMessage]:
        self.session.add_all(slack_messages)
        self.session.flush()
        return slack_messages

    def find_all_by_user_id_and_target_date(
        self, user_id: int, target_date: date
    ) -> list[SlackMessage]:
        stmt = (
            select(SlackMessage)
            .where(
                SlackMessage.user_id == user_id,
                SlackMessage.target_date == target_date,
            )
            .order_by(SlackMessage.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def delete_by_user_id_and_target_date(self, user_id: int, target_date: date) -> None:
        stmt = delete(SlackMessage).where(
            SlackMessage.user_id == user_id,
            SlackMessage.target_date == target_date,
        )
        self.session.execute(stmt)
        self.session.flush()
