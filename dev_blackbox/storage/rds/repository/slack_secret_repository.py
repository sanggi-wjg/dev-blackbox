from sqlalchemy import select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret


class SlackSecretRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, slack_secret: SlackSecret) -> SlackSecret:
        self.session.add(slack_secret)
        self.session.flush()
        return slack_secret

    def find_by_id(self, slack_secret_id: int) -> SlackSecret | None:
        stmt = select(SlackSecret).where(
            SlackSecret.id == slack_secret_id,
            SlackSecret.is_deleted.is_(False),
        )
        return self.session.scalar(stmt)

    def find_all(self) -> list[SlackSecret]:
        stmt = select(SlackSecret).where(SlackSecret.is_deleted.is_(False)).order_by(SlackSecret.id)
        return list(self.session.scalars(stmt))
