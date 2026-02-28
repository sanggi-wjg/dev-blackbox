from datetime import date
from typing import Callable
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from dev_blackbox.client.jira_client import JiraClient
from dev_blackbox.core.exception import (
    UserNotFoundException,
    JiraUserNotAssignedException,
    JiraUserProjectNotAssignedException,
)
from dev_blackbox.service.jira_event_service import JiraEventService
from dev_blackbox.storage.rds.entity.jira_event import JiraEvent
from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret
from dev_blackbox.storage.rds.entity.jira_user import JiraUser
from dev_blackbox.storage.rds.entity.user import User
from tests.fixtures.jira_fixture import create_jira_issue_raw


class JiraEventServiceTest:

    # ── get_jira_events ──

    def test_get_jira_events(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
        jira_event_fixture: Callable[..., JiraEvent],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(jira_secret_id=secret.id, user_id=user.id)
        target_date = date(2025, 1, 1)
        event = jira_event_fixture(
            user_id=user.id,
            jira_user_id=jira_user.id,
            target_date=target_date,
        )

        service = JiraEventService(db_session)

        # when
        result = service.get_jira_events(user.id, target_date)

        # then
        assert result == [event]

    def test_get_jira_events_이벤트가_없으면_빈_리스트(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = JiraEventService(db_session)

        # when
        result = service.get_jira_events(user.id, date(2025, 1, 1))

        # then
        assert result == []

    def test_get_jira_events_다른_날짜_이벤트는_조회되지_않음(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
        jira_event_fixture: Callable[..., JiraEvent],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(jira_secret_id=secret.id, user_id=user.id)
        jira_event_fixture(
            user_id=user.id,
            jira_user_id=jira_user.id,
            target_date=date(2025, 1, 2),
        )

        service = JiraEventService(db_session)

        # when
        result = service.get_jira_events(user.id, date(2025, 1, 1))

        # then
        assert result == []

    # ── save_jira_events ──

    def test_save_jira_events(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project="PROJ",
            account_id="account-1",
        )
        target_date = date(2025, 1, 1)

        # mock
        mock_issue = MagicMock()
        mock_issue.raw = create_jira_issue_raw(issue_id="10001", key="PROJ-1")

        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_search_issues.return_value = [mock_issue]

        mocker.patch.object(
            JiraEventService,
            "_get_user_or_throw",
            return_value=user,
        )
        mocker.patch(
            "dev_blackbox.service.jira_event_service.JiraSecretService.get_jira_client",
            return_value=mock_client,
        )

        service = JiraEventService(db_session)

        # when
        result = service.save_jira_events(user.id, target_date)

        # then
        assert len(result) == 1
        assert result[0].issue_id == "10001"
        assert result[0].issue_key == "PROJ-1"
        assert result[0].user_id == user.id
        assert result[0].jira_user_id == jira_user.id
        mock_client.fetch_search_issues.assert_called_once()

    def test_save_jira_events_API_응답이_비어있으면_빈_리스트(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project="PROJ",
            account_id="account-2",
        )
        target_date = date(2025, 1, 1)

        # mock
        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_search_issues.return_value = []

        mocker.patch.object(
            JiraEventService,
            "_get_user_or_throw",
            return_value=user,
        )
        mocker.patch(
            "dev_blackbox.service.jira_event_service.JiraSecretService.get_jira_client",
            return_value=mock_client,
        )

        service = JiraEventService(db_session)

        # when
        result = service.save_jira_events(user.id, target_date)

        # then
        assert result == []

    def test_save_jira_events_여러_이슈_저장(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project="PROJ",
            account_id="account-3",
        )
        target_date = date(2025, 1, 1)

        # mock
        mock_issue_1 = MagicMock()
        mock_issue_1.raw = create_jira_issue_raw(issue_id="10001", key="PROJ-1")
        mock_issue_2 = MagicMock()
        mock_issue_2.raw = create_jira_issue_raw(issue_id="10002", key="PROJ-2")

        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_search_issues.return_value = [mock_issue_1, mock_issue_2]

        mocker.patch.object(
            JiraEventService,
            "_get_user_or_throw",
            return_value=user,
        )
        mocker.patch(
            "dev_blackbox.service.jira_event_service.JiraSecretService.get_jira_client",
            return_value=mock_client,
        )

        service = JiraEventService(db_session)

        # when
        result = service.save_jira_events(user.id, target_date)

        # then
        assert len(result) == 2
        assert result[0].issue_key == "PROJ-1"
        assert result[1].issue_key == "PROJ-2"

    def test_save_jira_events_기존_데이터_삭제_후_재저장(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
        jira_event_fixture: Callable[..., JiraEvent],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project="PROJ",
            account_id="account-4",
        )
        target_date = date(2025, 1, 1)
        jira_event_fixture(
            user_id=user.id,
            jira_user_id=jira_user.id,
            target_date=target_date,
            issue_id="old-issue",
            issue_key="PROJ-OLD",
        )

        # mock
        mock_issue = MagicMock()
        mock_issue.raw = create_jira_issue_raw(issue_id="new-issue", key="PROJ-NEW")

        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_search_issues.return_value = [mock_issue]

        mocker.patch.object(
            JiraEventService,
            "_get_user_or_throw",
            return_value=user,
        )
        mocker.patch(
            "dev_blackbox.service.jira_event_service.JiraSecretService.get_jira_client",
            return_value=mock_client,
        )

        service = JiraEventService(db_session)

        # when
        result = service.save_jira_events(user.id, target_date)

        # then
        assert len(result) == 1
        assert result[0].issue_key == "PROJ-NEW"

    # ── save_jira_events 예외 케이스 ──

    def test_save_jira_events_사용자가_없으면_예외(
        self,
        db_session: Session,
    ):
        # given
        service = JiraEventService(db_session)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.save_jira_events(9999, date(2025, 1, 1))

    def test_save_jira_events_jira_user가_없으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = JiraEventService(db_session)

        # when & then
        with pytest.raises(JiraUserNotAssignedException):
            service.save_jira_events(user.id, date(2025, 1, 1))

    def test_save_jira_events_project가_없으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=user.id,
            project=None,
            account_id="account-no-project",
        )
        service = JiraEventService(db_session)

        # when & then
        with pytest.raises(JiraUserProjectNotAssignedException):
            service.save_jira_events(user.id, date(2025, 1, 1))
