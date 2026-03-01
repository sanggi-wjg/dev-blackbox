import logging
from datetime import date

from sqlalchemy.orm import Session

from dev_blackbox.client.github_client import GitHubClient
from dev_blackbox.client.model.github_api_model import (
    GithubCommitModel,
    GithubEventModel,
    GithubPushEventPayloadModel,
)
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import (
    UserNotFoundException,
    GitHubUserSecretNotSetException,
)
from dev_blackbox.storage.rds.entity import User
from dev_blackbox.storage.rds.entity.github_event import GitHubEvent
from dev_blackbox.storage.rds.repository import (
    GitHubEventRepository,
    UserRepository,
    GitHubUserSecretRepository,
)
from dev_blackbox.util.datetime_util import get_yesterday

logger = logging.getLogger(__name__)


class GitHubEventService:
    SUMMARY_EVENT_TYPES = ["PushEvent"]

    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)
        self.github_event_repository = GitHubEventRepository(session)
        self.github_user_secret_repository = GitHubUserSecretRepository(session)
        self.encrypt_service = get_encrypt_service()

    def get_events_by_user_id(self, user_id: int) -> list[GitHubEvent]:
        return self.github_event_repository.find_all_by_user_id(user_id)

    def get_github_events(
        self,
        user_id: int,
        target_date: date,
    ) -> list[GitHubEvent]:
        return self.github_event_repository.find_all_by_user_id_and_target_date(
            user_id, target_date
        )

    def get_github_events_by_event_types(
        self,
        user_id: int,
        target_date: date,
        event_types: list[str],
    ) -> list[GitHubEvent]:
        return self.github_event_repository.find_all_by_user_id_and_target_date_and_event_types(
            user_id,
            target_date,
            event_types,
        )

    def save_github_events(
        self,
        user_id: int,
        target_date: date | None = None,
    ) -> list[GitHubEvent]:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)

        # target_date가 없으면 유저 타임존 기준 어제 날짜로 설정
        if target_date is None:
            target_date = get_yesterday(user.tz_info)

        # 기존 데이터 삭제 후 갱신하도록
        self.github_event_repository.delete_by_user_id_and_target_date(user_id, target_date)

        # 없으면 에러
        github_user_secret = self.github_user_secret_repository.find_by_user_id(user_id=user.id)
        if github_user_secret is None:
            raise GitHubUserSecretNotSetException(user_id)

        # 복호화 하고
        decrypted_token = self.encrypt_service.decrypt(github_user_secret.personal_access_token)
        github_client = GitHubClient.create(token=decrypted_token)

        # 조회 하고
        events = []
        github_events = self.fetch_github_events(
            github_client=github_client,
            user=user,
            github_username=github_user_secret.username,
            target_date=target_date,
        )
        # 저장 ㄱㄱ
        for github_event in github_events:
            github_commit = self.fetch_github_commit_by_event(github_client, github_event)
            events.append(
                GitHubEvent.create(
                    user_id=user.id,
                    github_user_secret_id=github_user_secret.id,
                    target_date=target_date,
                    event=github_event,
                    commit=github_commit,
                ),
            )
        return self.github_event_repository.save_all(events)

    def fetch_github_events(
        self,
        github_client: GitHubClient,
        user: User,
        github_username: str,
        target_date: date,
    ) -> list[GithubEventModel]:
        """GitHub API를 통해 특정 사용자의 이벤트 조회. 모든 이벤트 타입을 반환한다."""
        github_events = github_client.fetch_events_by_date(
            username=github_username,
            target_date=target_date,
            tz_info=user.tz_info,
        )
        events = github_events.events
        if not events:
            logger.warning(f"No events found for {github_username}. (user_id: {user.id})")

        logger.info(f"Collected {len(events)} events for {github_username}. (user_id: {user.id})")
        return events

    def fetch_github_commit_by_event(
        self,
        github_client: GitHubClient,
        github_event: GithubEventModel,
    ) -> GithubCommitModel | None:
        """GitHub API를 통해 PushEvent의 커밋 정보 조회. 다른 이벤트 타입은 None 반환."""
        if not isinstance(github_event.typed_payload, GithubPushEventPayloadModel):
            return None

        payload = github_event.typed_payload
        commit = github_client.fetch_commit(
            repository_url=github_event.repo.url,
            sha=payload.head,
        )
        logger.info(f"Collected commit info for {github_event.id}.")
        return commit
