import logging

from dev_blackbox.client.github_client import GithubClient
from dev_blackbox.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GitHubCollectService:
    COLLECT_TYPES = ["PushEvent", "PullRequestEvent"]

    def __init__(self):
        token = settings.github.personal_access_token
        if not token:
            raise RuntimeError(
                "⚙️ GitHub configuration is incomplete. Please check the GITHUB environment variables."
            )

        self.github_client = GithubClient.create(token=token)

    def collect_yesterday_commit_info(self) -> list[str]:
        username = settings.github.username
        if not username:
            raise RuntimeError(
                "⚙️ GitHub configuration is incomplete. Please check the GITHUB environment variables."
            )

        commit_info = []
        events = self.github_client.fetch_events_by_date(
            username=username,
            tz_info=settings.tz_info,
            timedelta_days=1,
        )
        # fixme 테스트 중이라 3개 제한 해놓음
        events = [event for event in events.events if event.type in self.COLLECT_TYPES][:3]
        if not events:
            logger.warning(f"No events found for {username}.")
            return []

        for event in events:
            # todo: event_type 별로 따로 parse 로직 구현 하면 좋을 듯?
            if event.is_type_push_event():
                payload = event.get_push_event_payload()
                commit = self.github_client.fetch_commit(
                    repository_url=event.repo.url, sha=payload.head
                )
                commit_info.append(commit.detail_text)
            # 우선 PushEvent만 진행해보고 이후 판단
            # if event.is_type_pull_request_event():
            #     payload = event.get_pull_request_event_payload()
            #     print(payload)

        if not commit_info:
            logger.warning(f"No commit details found for {username}.")
        return commit_info
