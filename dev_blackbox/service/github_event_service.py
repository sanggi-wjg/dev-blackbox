from datetime import date

from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.github_event import GitHubEvent
from dev_blackbox.storage.rds.repository import GitHubEventRepository


class GitHubEventService:

    def __init__(self, session: Session):
        self.github_event_repository = GitHubEventRepository(session)

    def get_events_by_user_id(self, user_id: int) -> list[GitHubEvent]:
        return self.github_event_repository.find_all_by_user_id(user_id)

    def get_github_events(self, user_id: int, target_date: date) -> list[GitHubEvent]:
        return self.github_event_repository.find_all_by_user_id_and_target_date(
            user_id, target_date
        )
