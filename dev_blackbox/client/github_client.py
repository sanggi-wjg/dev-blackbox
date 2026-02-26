import logging
from datetime import date
from zoneinfo import ZoneInfo

import httpx

from dev_blackbox.client.model.github_api_model import GithubEventModelList, GithubCommitModel

logger = logging.getLogger(__name__)


class GitHubClient:
    LIMIT_EVENTS_PAGE = 4
    LIMIT_EVENTS_TOLERANCE = 5

    def __init__(self, token: str):
        self._token = token
        self._headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    @classmethod
    def create(cls, token: str):
        return cls(token=token)

    def fetch_events(
        self, username: str, page: int = 1, per_page: int = 30
    ) -> GithubEventModelList:
        """
        https://docs.github.com/ko/rest/activity/events?apiVersion=2022-11-28#list-events-for-the-authenticated-user

        이벤트 조회
        """
        endpoint = f"https://api.github.com/users/{username}/events"
        params = {
            "page": page,
            "per_page": per_page,
        }

        try:
            with httpx.Client() as client:
                response = client.get(endpoint, headers=self._headers, params=params)
                response.raise_for_status()
                return GithubEventModelList.model_validate({"events": response.json()})
        except httpx.HTTPError:
            logger.warning(f"Failed to fetch events for {username}.")
            raise

    def fetch_events_by_date(
        self,
        username: str,
        target_date: date,
        tz_info: ZoneInfo,
    ) -> GithubEventModelList:
        result = []
        page = 1
        tolerance = 0

        while True:
            github_events = self.fetch_events(username, page=page, per_page=100)
            if not github_events.events:
                break

            for event in github_events.events:
                event_date = event.get_created_date(tz_info)

                if event_date == target_date:
                    result.append(event)
                elif event_date < target_date:
                    tolerance += 1

                # 과거 이벤트를 한참 뒤에 처리하는 경우도 가끔 있어서 tolerance 기준을 좀 느슨하게 잡음
                if tolerance > self.LIMIT_EVENTS_TOLERANCE:
                    return GithubEventModelList(events=result)

            page += 1
            # 일정 페이징 요청 제한
            if page >= self.LIMIT_EVENTS_PAGE:
                logger.warning(
                    f"Reached maximum page {page} for date {target_date} in github events."
                )
                break

        return GithubEventModelList(events=result)

    def fetch_commit(self, repository_url: str, sha: str) -> GithubCommitModel:
        """
        https://docs.github.com/ko/rest/commits/commits?apiVersion=2022-11-28#get-a-commit

        커밋 조회
        """
        endpoint = repository_url + f"/commits/{sha}"

        try:
            with httpx.Client() as client:
                response = client.get(endpoint, headers=self._headers)
                response.raise_for_status()
                return GithubCommitModel.model_validate(response.json())
        except httpx.HTTPError:
            logger.warning(f"Failed to fetch commit {sha} in {repository_url}.")
            raise
