from sqlalchemy import select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret


class JiraSecretRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, jira_secret: JiraSecret) -> JiraSecret:
        self.session.add(jira_secret)
        self.session.flush()
        return jira_secret

    def find_by_id(self, jira_secret_id: int) -> JiraSecret | None:
        stmt = select(JiraSecret).where(
            JiraSecret.id == jira_secret_id,
            JiraSecret.is_deleted.is_(False),
        )
        return self.session.scalar(stmt)

    def find_all(self) -> list[JiraSecret]:
        stmt = select(JiraSecret).where(JiraSecret.is_deleted.is_(False)).order_by(JiraSecret.id)
        return list(self.session.scalars(stmt).all())
