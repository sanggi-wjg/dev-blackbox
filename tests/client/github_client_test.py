from datetime import date
from zoneinfo import ZoneInfo

import pytest
from httpx import HTTPError

from dev_blackbox.client.github_client import GitHubClient
from dev_blackbox.client.model.github_api_model import GithubEventModelList
from tests.fixtures.github_fixture import create_github_commit_model, create_github_event_model


class GitHubClientTest:

    def setup_method(self):
        self.github_client = GitHubClient("ghp_test_token")

    def test_fetch_events(self, httpx_mock):
        # given
        expected_events = GithubEventModelList(
            events=[
                create_github_event_model("1"),
                create_github_event_model("2"),
            ]
        )

        # mock
        httpx_mock.add_response(
            status_code=200,
            json=[e.model_dump(mode="json") for e in expected_events.events],
        )

        # when
        result = self.github_client.fetch_events("test")

        # then
        assert result == expected_events

    def test_fetch_events_on_error(self, httpx_mock):
        # mock
        httpx_mock.add_response(
            status_code=400,
        )

        # when
        with pytest.raises(HTTPError):
            self.github_client.fetch_events("test")

    def test_fetch_events_by_date(self, httpx_mock):
        # given
        target_date = date(2025, 1, 1)
        tz_info = ZoneInfo("UTC")

        matching_events = [
            create_github_event_model("1", created_at="2025-01-01T10:00:00Z"),
            create_github_event_model("2", created_at="2025-01-01T15:00:00Z"),
        ]
        old_events = [
            create_github_event_model(str(i), created_at="2024-12-31T00:00:00Z")
            for i in range(3, 9)  # 6개 → tolerance > LIMIT_EVENTS_TOLERANCE(5)
        ]

        # mock
        httpx_mock.add_response(
            status_code=200,
            json=[e.model_dump(mode="json") for e in matching_events + old_events],
        )

        # when
        result = self.github_client.fetch_events_by_date("test", target_date, tz_info)

        # then
        assert result == GithubEventModelList(events=matching_events)

    def test_fetch_commit(self, httpx_mock):
        # given
        expected_commit = create_github_commit_model(sha="abc123")

        # mock
        httpx_mock.add_response(
            status_code=200,
            json=expected_commit.model_dump(mode="json"),
        )

        # when
        result = self.github_client.fetch_commit("https://api.github.com/repos/test/repo", "abc123")

        # then
        assert result == expected_commit

    def test_fetch_commit_on_error(self, httpx_mock):
        # mock
        httpx_mock.add_response(
            status_code=400,
        )

        # when
        with pytest.raises(HTTPError):
            self.github_client.fetch_commit("https://api.github.com/repos/test/repo", "abc123")
