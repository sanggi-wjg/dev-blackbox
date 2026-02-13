import logging

from sqlalchemy.orm import Session

from dev_blackbox.client.github_client import GithubClient
from dev_blackbox.service.github_user_secret_service import GitHubUserSecretService
from dev_blackbox.storage.rds.repository.user_repository import UserRepository
from dev_blackbox.core.exception import UserByIdNotFoundException

logger = logging.getLogger(__name__)


class GitHubCollectService:
    COLLECT_TYPES = ["PushEvent", "PullRequestEvent"]

    def __init__(self, session: Session):
        self.session = session
        self.secret_service = GitHubUserSecretService(session)
        self.user_repository = UserRepository(session)

    def collect_yesterday_commit_info(self, user_id: int) -> list[str]:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserByIdNotFoundException(user_id)

        username, token = self.secret_service.get_decrypted_token(user_id)
        github_client = GithubClient.create(token=token)

        commit_info = []
        events = github_client.fetch_events_by_date(
            username=username,
            tz_info=user.tz_info,
            timedelta_days=1,
        )

        events = [event for event in events.events if event.type in self.COLLECT_TYPES]
        if not events:
            logger.warning(f"No events found for {username}.")
            return []

        for event in events:
            # 이후 event_type 추기사 별도 parse 로직 구현 필요
            # 현재는 우선 PushEvent만 진행
            if event.is_type_push_event():
                payload = event.get_push_event_payload()
                commit = github_client.fetch_commit(repository_url=event.repo.url, sha=payload.head)
                commit_info.append(commit.detail_text)

        if not commit_info:
            logger.warning(f"No commit details found for {username}.")
        return commit_info
