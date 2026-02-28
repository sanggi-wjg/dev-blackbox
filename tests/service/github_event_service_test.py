from datetime import date
from unittest.mock import MagicMock

import pytest

from dev_blackbox.client.github_client import GitHubClient
from dev_blackbox.client.model.github_api_model import (
    GithubCommitModel,
    GithubEventModelList,
)
from dev_blackbox.core.exception import (
    GitHubUserSecretNotSetException,
    UserNotFoundException,
)
from dev_blackbox.service.github_event_service import GitHubEventService
from tests.fixtures.github_fixture import create_github_event_model


class GitHubEventServiceTest:

    def test_get_events_by_user_id(
        self,
        db_session,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)
        event = github_event_fixture(user_id=user.id, github_user_secret_id=secret.id)

        service = GitHubEventService(db_session)

        # when
        result = service.get_events_by_user_id(user.id)

        # then
        assert result == [event]

    def test_get_events_by_user_id_이벤트가_없으면_빈_리스트(self, db_session, user_fixture):
        # given
        user = user_fixture()
        service = GitHubEventService(db_session)

        # when
        result = service.get_events_by_user_id(user.id)

        # then
        assert result == []

    def test_get_github_events(
        self,
        db_session,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        target_date = date(2025, 1, 1)
        another_date = date(2025, 1, 2)

        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)
        event = github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=target_date,
            event_id="event-id",
        )
        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=another_date,
            event_id="another-event-id",
        )

        service = GitHubEventService(db_session)

        # when
        result = service.get_github_events(user.id, target_date)

        # then
        assert result == [event]

    def test_get_github_events_이벤트가_없으면_빈_리스트(self, db_session, user_fixture):
        # given
        user = user_fixture()
        service = GitHubEventService(db_session)

        # when
        result = service.get_github_events(
            user.id,
            date(2025, 1, 1),
        )

        # then
        assert result == []

    def test_get_github_events_by_event_types(
        self,
        db_session,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        target_date = date(2025, 1, 1)
        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)
        push_event = github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=target_date,
            event_type="PushEvent",
        )
        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=target_date,
            event_type="PullRequestEvent",
        )

        service = GitHubEventService(db_session)

        # when
        result = service.get_github_events_by_event_types(user.id, target_date, ["PushEvent"])

        # then
        assert result == [push_event]

    def test_get_github_events_by_event_types_이벤트가_없으면_빈_리스트(
        self,
        db_session,
        user_fixture,
    ):
        # given
        user = user_fixture()
        service = GitHubEventService(db_session)

        # when
        result = service.get_github_events_by_event_types(user.id, date(2025, 1, 1), ["PushEvent"])

        # then
        assert result == []

    def test_save_github_events_사용자가_없으면_예외(self, db_session):
        # given
        service = GitHubEventService(db_session)
        target_date = date(2025, 1, 1)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.save_github_events(9999, target_date)

    def test_save_github_events_시크릿이_없으면_예외(self, db_session, user_fixture):
        # given
        service = GitHubEventService(db_session)
        user = user_fixture()
        target_date = date(2025, 1, 1)

        # when & then
        with pytest.raises(GitHubUserSecretNotSetException):
            service.save_github_events(user.id, target_date)

    def test_save_github_events_이벤트가_없으면_빈_리스트(
        self,
        mocker,
        db_session,
        user_fixture,
        github_user_secret_fixture,
    ):
        # given
        user = user_fixture()
        github_user_secret_fixture(user_id=user.id)

        service = GitHubEventService(db_session)
        target_date = date(2025, 1, 1)

        # mock
        mock_client = MagicMock(spec=GitHubClient)
        mock_client.fetch_events_by_date.return_value = GithubEventModelList(events=[])

        mocker.patch(
            "dev_blackbox.service.github_event_service.GitHubClient.create",
            return_value=mock_client,
        )

        # when
        result = service.save_github_events(user.id, target_date)

        # then
        assert result == []
        mock_client.fetch_commit.assert_not_called()

    def test_save_github_events(
        self,
        mocker,
        db_session,
        user_fixture,
        github_user_secret_fixture,
    ):
        # given
        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)

        service = GitHubEventService(db_session)
        target_date = date(2025, 1, 1)

        # mock
        event_model = create_github_event_model(event_id="evt-save")

        mock_commit = MagicMock(spec=GithubCommitModel)
        mock_commit.model_dump.return_value = {"sha": "abc123"}

        mock_client = MagicMock(spec=GitHubClient)
        mock_client.fetch_events_by_date.return_value = GithubEventModelList(
            events=[event_model],
        )
        mock_client.fetch_commit.return_value = mock_commit

        mocker.patch(
            "dev_blackbox.service.github_event_service.GitHubClient.create",
            return_value=mock_client,
        )

        # when
        result = service.save_github_events(user.id, target_date)

        # then
        assert len(result) == 1
        assert result[0].event_id == event_model.id
        assert result[0].user_id == user.id
        assert result[0].commit is not None

        mock_client.fetch_events_by_date.assert_called_once_with(
            username=secret.username,
            target_date=target_date,
            tz_info=user.tz_info,
        )
        mock_client.fetch_commit.assert_called_once()
