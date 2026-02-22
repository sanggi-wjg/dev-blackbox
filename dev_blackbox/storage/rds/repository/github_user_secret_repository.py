from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.github_user_secret import GitHubUserSecret


class GitHubUserSecretRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, secret: GitHubUserSecret) -> GitHubUserSecret:
        self.session.add(secret)
        self.session.flush()
        return secret

    def find_by_user_id(self, user_id: int) -> GitHubUserSecret | None:
        stmt = select(GitHubUserSecret).where(GitHubUserSecret.user_id == user_id)
        return self.session.scalar(stmt)

    def delete(self, secret: GitHubUserSecret) -> None:
        self.session.delete(secret)
        self.session.flush()
