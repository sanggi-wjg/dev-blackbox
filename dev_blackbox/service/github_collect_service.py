import logging
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from dev_blackbox.client.github_client import GithubClient
from dev_blackbox.client.model.github_model import GithubCommitModel, GithubEventModel
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import UserByIdNotFoundException
from dev_blackbox.storage.rds.entity import User, GitHubEvent
from dev_blackbox.storage.rds.repository import GitHubUserSecretRepository
from dev_blackbox.storage.rds.repository.github_event_repository import GitHubEventRepository
from dev_blackbox.storage.rds.repository.user_repository import UserRepository

logger = logging.getLogger(__name__)


class GitHubCollectService:
    COLLECT_TYPES = ["PushEvent"]

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.github_event_repository = GitHubEventRepository(session)
        self.github_user_secret_repository = GitHubUserSecretRepository(session)
        self.encrypt_service = get_encrypt_service()

    def save_github_events(
        self, user_id: int, target_date: date | None = None
    ) -> list[GitHubEvent]:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserByIdNotFoundException(user_id)

        # target_date가 없으면 유저 타임존 기준 어제 날짜로 설정
        if target_date is None:
            target_date = datetime.now(user.tz_info).date() - timedelta(days=1)

        # 기존 데이터 삭제 후 갱신하도록
        self.github_event_repository.delete_by_user_id_and_target_date(user_id, target_date)

        github_user_secret = self.github_user_secret_repository.find_by_user_id(user_id=user.id)
        if github_user_secret is None:
            logger.warning(f"GitHub User Secret not found. (user_id: {user.id})")
            return []

        decrypted_token = self.encrypt_service.decrypt(github_user_secret.personal_access_token)
        github_client = GithubClient.create(token=decrypted_token)

        events = []
        github_events = self.get_github_events(
            github_client=github_client,
            user=user,
            github_username=github_user_secret.username,
            target_date=target_date,
        )
        for github_event in github_events:
            github_commit = self.get_github_commit_by_event(github_client, github_event)
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

    def get_github_events(
        self,
        github_client: GithubClient,
        user: User,
        github_username: str,
        target_date: date,
    ) -> list[GithubEventModel]:
        """
        GitHub API를 통해 특정 사용자의 이벤트 조회.

        지정된 날짜의 이벤트만 조회하며, COLLECT_TYPES에 정의된 타입의 이벤트만 필터링합니다.
        """
        github_events = github_client.fetch_events_by_date(
            username=github_username,
            target_date=target_date,
            tz_info=user.tz_info,
        )
        # 나중에 타입 추가 된다면 상위 메소드에서 filter 메소드로 필터링해서 commit 정보 가져오도록 하는게 좋아보임, 우선은 여기서 필터 처리
        github_events = [
            event for event in github_events.events if event.type in self.COLLECT_TYPES
        ]
        if not github_events:
            logger.warning(f"No events found for {github_username}. (user_id: {user.id})")

        logger.info(
            f"Collected {len(github_events)} events for {github_username}. (user_id: {user.id})"
        )
        return github_events

    def get_github_commit_by_event(
        self,
        github_client: GithubClient,
        github_event: GithubEventModel,
    ) -> GithubCommitModel | None:
        """
        GitHub API를 통해 특정 이벤트의 커밋 정보 조회.

        [편지]
        event_type 추가시 별도 parse 로직 구현 필요
        현재는 우선 PushEvent만 진행
        """
        if github_event.is_type_push_event():
            payload = github_event.get_push_event_payload()
            commit = github_client.fetch_commit(
                repository_url=github_event.repo.url,
                sha=payload.head,
            )
            logger.info(f"Collected commit info for {github_event.id}.")
            return commit

        logger.info(f"No commit info found for {github_event.id}.")
        return None
