from typing import Callable
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from dev_blackbox.client.slack_client import SlackClient
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import SlackSecretNotFoundException
from dev_blackbox.service.command.slack_secret_command import CreateSlackSecretCommand
from dev_blackbox.service.slack_secret_service import SlackSecretService
from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret


class SlackSecretServiceTest:

    def test_create_secret(
        self,
        db_session: Session,
    ):
        # given
        service = SlackSecretService(db_session)
        command = CreateSlackSecretCommand(
            name="My Slack",
            bot_token="xoxb-secret-token-123",
        )
        encrypt_service = get_encrypt_service()

        # when
        result = service.create_secret(command)

        # then
        assert result.name == command.name
        assert encrypt_service.decrypt(result.bot_token) == command.bot_token

    def test_get_secrets(
        self,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        secret = slack_secret_fixture()
        service = SlackSecretService(db_session)

        # when
        result = service.get_secrets()

        # then
        assert secret in result

    def test_get_secrets_비어있으면_빈_리스트(
        self,
        db_session: Session,
    ):
        # given
        service = SlackSecretService(db_session)

        # when
        result = service.get_secrets()

        # then
        assert result == []

    def test_get_secret_by_id_or_throw(
        self,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        secret = slack_secret_fixture()
        service = SlackSecretService(db_session)

        # when
        result = service.get_secret_by_id_or_throw(secret.id)

        # then
        assert result == secret

    def test_get_secret_by_id_or_throw_존재하지_않으면_예외(
        self,
        db_session: Session,
    ):
        # given
        service = SlackSecretService(db_session)

        # when & then
        with pytest.raises(SlackSecretNotFoundException):
            service.get_secret_by_id_or_throw(9999)

    def test_delete_secret(
        self,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        secret = slack_secret_fixture()
        service = SlackSecretService(db_session)

        # when
        service.delete_secret(secret.id)

        # then
        assert secret.is_deleted is True
        assert secret.deleted_at is not None

    def test_delete_secret_존재하지_않으면_예외(
        self,
        db_session: Session,
    ):
        # given
        service = SlackSecretService(db_session)

        # when & then
        with pytest.raises(SlackSecretNotFoundException):
            service.delete_secret(9999)

    def test_get_slack_client(
        self,
        mocker,
        db_session: Session,
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        secret = slack_secret_fixture()
        service = SlackSecretService(db_session)

        # mock
        mock_client = MagicMock(spec=SlackClient)
        mocker.patch(
            "dev_blackbox.service.slack_secret_service.get_slack_client",
            return_value=mock_client,
        )

        # when
        result = service.get_slack_client(secret)

        # then
        assert result == mock_client
