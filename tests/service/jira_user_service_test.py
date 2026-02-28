from typing import Callable
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from dev_blackbox.client.jira_client import JiraClient
from dev_blackbox.core.exception import (
    JiraSecretNotFoundException,
    JiraUserNotFoundException,
    JiraUserSecretMismatchException,
    UserNotFoundException,
)
from dev_blackbox.service.jira_user_service import JiraUserService
from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret
from dev_blackbox.storage.rds.entity.jira_user import JiraUser
from dev_blackbox.storage.rds.entity.user import User


class JiraUserServiceTest:

    # ── get_jira_users ──

    def test_get_jira_users(
        self,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(jira_secret_id=secret.id)
        service = JiraUserService(db_session)

        # when
        result = service.get_jira_users()

        # then
        assert jira_user in result

    def test_get_jira_users_secret_id로_필터링(
        self,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        secret1 = jira_secret_fixture(name="Secret 1")
        secret2 = jira_secret_fixture(name="Secret 2")
        user1 = jira_user_fixture(jira_secret_id=secret1.id, account_id="acc-1")
        jira_user_fixture(jira_secret_id=secret2.id, account_id="acc-2")
        service = JiraUserService(db_session)

        # when
        result = service.get_jira_users(jira_secret_id=secret1.id)

        # then
        assert result == [user1]

    def test_get_jira_users_비어있으면_빈_리스트(
        self,
        db_session: Session,
    ):
        # given
        service = JiraUserService(db_session)

        # when
        result = service.get_jira_users()

        # then
        assert result == []

    # ── sync_jira_users ──

    def test_sync_jira_users(
        self,
        mocker,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        secret = jira_secret_fixture()
        service = JiraUserService(db_session)

        # mock
        mock_jira_user = MagicMock()
        mock_jira_user.accountId = "new-account-id"
        mock_jira_user.active = True
        mock_jira_user.displayName = "New User"
        mock_jira_user.emailAddress = "new@dev.com"
        mock_jira_user.self = "https://test.atlassian.net/user/new"

        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_assignable_users.return_value = [mock_jira_user]

        mocker.patch(
            "dev_blackbox.service.jira_user_service.JiraSecretService.get_jira_client",
            return_value=mock_client,
        )

        # when
        result = service.sync_jira_users(secret.id, "PROJ")

        # then
        assert len(result) == 1
        assert result[0].account_id == "new-account-id"
        mock_client.fetch_assignable_users.assert_called_once_with(project="PROJ")

    def test_sync_jira_users_기존_사용자는_건너뜀(
        self,
        mocker,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        secret = jira_secret_fixture()
        jira_user_fixture(jira_secret_id=secret.id, account_id="existing-account")
        service = JiraUserService(db_session)

        # mock
        mock_existing_user = MagicMock()
        mock_existing_user.accountId = "existing-account"
        mock_existing_user.active = True
        mock_existing_user.displayName = "Existing"
        mock_existing_user.emailAddress = "existing@dev.com"
        mock_existing_user.self = "https://test.atlassian.net/user/existing"

        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_assignable_users.return_value = [mock_existing_user]

        mocker.patch(
            "dev_blackbox.service.jira_user_service.JiraSecretService.get_jira_client",
            return_value=mock_client,
        )

        # when
        result = service.sync_jira_users(secret.id, "PROJ")

        # then
        assert result == []

    def test_sync_jira_users_API_응답이_비어있으면_빈_리스트(
        self,
        mocker,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        secret = jira_secret_fixture()
        service = JiraUserService(db_session)

        # mock
        mock_client = MagicMock(spec=JiraClient)
        mock_client.fetch_assignable_users.return_value = []

        mocker.patch(
            "dev_blackbox.service.jira_user_service.JiraSecretService.get_jira_client",
            return_value=mock_client,
        )

        # when
        result = service.sync_jira_users(secret.id, "PROJ")

        # then
        assert result == []

    def test_sync_jira_users_존재하지_않는_시크릿이면_예외(
        self,
        db_session: Session,
    ):
        # given
        service = JiraUserService(db_session)

        # when & then
        with pytest.raises(JiraSecretNotFoundException):
            service.sync_jira_users(9999, "PROJ")

    # ── assign_user ──

    def test_assign_user(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(jira_secret_id=secret.id)
        service = JiraUserService(db_session)

        # when
        result = service.assign_user(user.id, secret.id, jira_user.id, "PROJ")

        # then
        assert result.user_id == user.id
        assert result.project == "PROJ"

    def test_assign_user_사용자가_없으면_예외(
        self,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(jira_secret_id=secret.id)
        service = JiraUserService(db_session)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.assign_user(9999, secret.id, jira_user.id, "PROJ")

    def test_assign_user_jira_user가_없으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        user = user_fixture()
        secret = jira_secret_fixture()
        service = JiraUserService(db_session)

        # when & then
        with pytest.raises(JiraUserNotFoundException):
            service.assign_user(user.id, secret.id, 9999, "PROJ")

    def test_assign_user_시크릿_불일치_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
    ):
        # given
        user = user_fixture()
        secret1 = jira_secret_fixture(name="Secret 1")
        secret2 = jira_secret_fixture(name="Secret 2")
        jira_user = jira_user_fixture(jira_secret_id=secret1.id)
        service = JiraUserService(db_session)

        # when & then
        with pytest.raises(JiraUserSecretMismatchException):
            service.assign_user(user.id, secret2.id, jira_user.id, "PROJ")

    # ── unassign_user ──

    def test_unassign_user(
        self,
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
        )
        service = JiraUserService(db_session)

        # when
        result = service.unassign_user(user.id, jira_user.id)

        # then
        assert result.user_id is None
        assert result.project is None

    def test_unassign_user_사용자가_없으면_예외(
        self,
        db_session: Session,
    ):
        # given
        service = JiraUserService(db_session)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.unassign_user(9999, 1)

    def test_unassign_user_jira_user가_없으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = JiraUserService(db_session)

        # when & then
        with pytest.raises(JiraUserNotFoundException):
            service.unassign_user(user.id, 9999)
