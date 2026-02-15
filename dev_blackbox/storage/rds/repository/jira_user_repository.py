from sqlalchemy import select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.jira_user import JiraUser


class JiraUserRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, jira_user: JiraUser) -> JiraUser:
        self.session.add(jira_user)
        self.session.flush()
        return jira_user

    def save_all(self, jira_users: list[JiraUser]) -> list[JiraUser]:
        self.session.add_all(jira_users)
        self.session.flush()
        return jira_users

    def find_by_user_id(self, user_id: int) -> list[JiraUser]:
        stmt = select(JiraUser).where(JiraUser.user_id == user_id)
        return list(self.session.scalars(stmt).all())

    def find_by_account_id(self, account_id: str) -> JiraUser | None:
        stmt = select(JiraUser).where(JiraUser.account_id == account_id)
        return self.session.scalar(stmt)

    def find_by_account_ids(self, account_ids: list[str]) -> list[JiraUser]:
        stmt = select(JiraUser).where(JiraUser.account_id.in_(account_ids))
        return list(self.session.scalars(stmt).all())
