from sqlalchemy import select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.slack_user import SlackUser


class SlackUserRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, slack_user: SlackUser) -> SlackUser:
        self.session.add(slack_user)
        self.session.flush()
        return slack_user

    def save_all(self, slack_users: list[SlackUser]) -> list[SlackUser]:
        self.session.add_all(slack_users)
        self.session.flush()
        return slack_users

    def find_by_id(self, slack_user_id: int) -> SlackUser | None:
        stmt = select(SlackUser).where(SlackUser.id == slack_user_id)
        return self.session.scalar(stmt)

    def find_by_user_id(self, user_id: int) -> SlackUser | None:
        stmt = select(SlackUser).where(SlackUser.user_id == user_id)
        return self.session.scalar(stmt)

    def find_all(self) -> list[SlackUser]:
        stmt = select(SlackUser).order_by(SlackUser.id)
        return list(self.session.scalars(stmt).all())

    def find_all_by_slack_secret_id(self, slack_secret_id: int) -> list[SlackUser]:
        stmt = (
            select(SlackUser)
            .where(SlackUser.slack_secret_id == slack_secret_id)
            .order_by(SlackUser.id)
        )
        return list(self.session.scalars(stmt).all())

    def find_by_slack_secret_id_and_member_ids(
        self, slack_secret_id: int, member_ids: list[str]
    ) -> list[SlackUser]:
        stmt = select(SlackUser).where(
            SlackUser.slack_secret_id == slack_secret_id,
            SlackUser.member_id.in_(member_ids),
        )
        return list(self.session.scalars(stmt).all())
