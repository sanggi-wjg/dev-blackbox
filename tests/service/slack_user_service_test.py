from typing import Callable
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from dev_blackbox.client.slack_client import SlackClient
from dev_blackbox.core.exception import (
    SlackSecretNotFoundException,
    SlackUserNotFoundException,
    SlackUserSecretMismatchException,
    UserNotFoundException,
)
from dev_blackbox.service.slack_user_service import SlackUserService
from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret
from dev_blackbox.storage.rds.entity.slack_user import SlackUser
from dev_blackbox.storage.rds.entity.user import User


class SlackUserServiceTest:

    # ── get_slack_users ──

    def test_get_slack_users(
        self,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(slack_secret_id=secret.id)
        service = SlackUserService(db_session)

        # when
        result = service.get_slack_users()

        # then
        assert slack_user in result

    def test_get_slack_users_secret_id로_필터링(
        self,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        secret1 = slack_secret_fixture(name="Slack 1")
        secret2 = slack_secret_fixture(name="Slack 2")
        user1 = slack_user_fixture(slack_secret_id=secret1.id, member_id="U001")
        slack_user_fixture(slack_secret_id=secret2.id, member_id="U002")
        service = SlackUserService(db_session)

        # when
        result = service.get_slack_users(slack_secret_id=secret1.id)

        # then
        assert result == [user1]

    def test_get_slack_users_비어있으면_빈_리스트(
        self,
        db_session: Session,
    ):
        # given
        service = SlackUserService(db_session)

        # when
        result = service.get_slack_users()

        # then
        assert result == []

    # ── sync_slack_users ──

    def test_sync_slack_users(
        self,
        mocker,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        secret = slack_secret_fixture()
        service = SlackUserService(db_session)

        # mock
        mock_client = MagicMock(spec=SlackClient)
        mock_client.fetch_users.return_value = [
            {
                "id": "U_NEW",
                "deleted": False,
                "real_name": "New User",
                "profile": {
                    "display_name": "newuser",
                    "real_name": "New User",
                    "email": "new@dev.com",
                },
            }
        ]

        mocker.patch(
            "dev_blackbox.service.slack_user_service.SlackSecretService.get_slack_client",
            return_value=mock_client,
        )

        # when
        result = service.sync_slack_users(secret.id)

        # then
        assert len(result) == 1
        assert result[0].member_id == "U_NEW"
        mock_client.fetch_users.assert_called_once_with(filter_bot=True)

    def test_sync_slack_users_기존_사용자는_건너뜀(
        self,
        mocker,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        secret = slack_secret_fixture()
        slack_user_fixture(slack_secret_id=secret.id, member_id="U_EXISTING")
        service = SlackUserService(db_session)

        # mock
        mock_client = MagicMock(spec=SlackClient)
        mock_client.fetch_users.return_value = [
            {
                "id": "U_EXISTING",
                "deleted": False,
                "real_name": "Existing",
                "profile": {
                    "display_name": "existing",
                    "real_name": "Existing",
                    "email": "existing@dev.com",
                },
            }
        ]

        mocker.patch(
            "dev_blackbox.service.slack_user_service.SlackSecretService.get_slack_client",
            return_value=mock_client,
        )

        # when
        result = service.sync_slack_users(secret.id)

        # then
        assert result == []

    def test_sync_slack_users_API_응답이_비어있으면_빈_리스트(
        self,
        mocker,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        secret = slack_secret_fixture()
        service = SlackUserService(db_session)

        # mock
        mock_client = MagicMock(spec=SlackClient)
        mock_client.fetch_users.return_value = []

        mocker.patch(
            "dev_blackbox.service.slack_user_service.SlackSecretService.get_slack_client",
            return_value=mock_client,
        )

        # when
        result = service.sync_slack_users(secret.id)

        # then
        assert result == []

    def test_sync_slack_users_존재하지_않는_시크릿이면_예외(
        self,
        db_session: Session,
    ):
        # given
        service = SlackUserService(db_session)

        # when & then
        with pytest.raises(SlackSecretNotFoundException):
            service.sync_slack_users(9999)

    # ── assign_user ──

    def test_assign_user(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        user = user_fixture()
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(slack_secret_id=secret.id)
        service = SlackUserService(db_session)

        # when
        result = service.assign_user(user.id, secret.id, slack_user.id)

        # then
        assert result.user_id == user.id

    def test_assign_user_사용자가_없으면_예외(
        self,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(slack_secret_id=secret.id)
        service = SlackUserService(db_session)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.assign_user(9999, secret.id, slack_user.id)

    def test_assign_user_slack_user가_없으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        user = user_fixture()
        secret = slack_secret_fixture()
        service = SlackUserService(db_session)

        # when & then
        with pytest.raises(SlackUserNotFoundException):
            service.assign_user(user.id, secret.id, 9999)

    def test_assign_user_시크릿_불일치_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        user = user_fixture()
        secret1 = slack_secret_fixture(name="Slack 1")
        secret2 = slack_secret_fixture(name="Slack 2")
        slack_user = slack_user_fixture(slack_secret_id=secret1.id)
        service = SlackUserService(db_session)

        # when & then
        with pytest.raises(SlackUserSecretMismatchException):
            service.assign_user(user.id, secret2.id, slack_user.id)

    # ── unassign_user ──

    def test_unassign_user(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        user = user_fixture()
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(
            slack_secret_id=secret.id,
            user_id=user.id,
        )
        service = SlackUserService(db_session)

        # when
        result = service.unassign_user(user.id, slack_user.id)

        # then
        assert result.user_id is None

    def test_unassign_user_사용자가_없으면_예외(
        self,
        db_session: Session,
    ):
        # given
        service = SlackUserService(db_session)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.unassign_user(9999, 1)

    def test_unassign_user_slack_user가_없으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = SlackUserService(db_session)

        # when & then
        with pytest.raises(SlackUserNotFoundException):
            service.unassign_user(user.id, 9999)
