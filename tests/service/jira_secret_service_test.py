from typing import Callable
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from dev_blackbox.client.jira_client import JiraClient
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import JiraSecretNotFoundException
from dev_blackbox.service.command.jira_secret_command import CreateJiraSecretCommand
from dev_blackbox.service.jira_secret_service import JiraSecretService
from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret


class JiraSecretServiceTest:

    def test_create_secret(
        self,
        db_session: Session,
    ):
        # given
        service = JiraSecretService(db_session)
        command = CreateJiraSecretCommand(
            name="My Jira",
            url="https://my.atlassian.net",
            username="admin",
            api_token="secret_token_123",
        )
        encrypt_service = get_encrypt_service()

        # when
        result = service.create_secret(command)

        # then
        assert result.name == command.name
        assert result.url == command.url
        assert encrypt_service.decrypt(result.username) == command.username
        assert encrypt_service.decrypt(result.api_token) == command.api_token

    def test_get_secrets(
        self,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        secret = jira_secret_fixture()
        service = JiraSecretService(db_session)

        # when
        result = service.get_secrets()

        # then
        assert secret in result

    def test_get_secrets_비어있으면_빈_리스트(
        self,
        db_session: Session,
    ):
        # given
        service = JiraSecretService(db_session)

        # when
        result = service.get_secrets()

        # then
        assert result == []

    def test_get_secret_by_id_or_throw(
        self,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        secret = jira_secret_fixture()
        service = JiraSecretService(db_session)

        # when
        result = service.get_secret_by_id_or_throw(secret.id)

        # then
        assert result == secret

    def test_get_secret_by_id_or_throw_존재하지_않으면_예외(
        self,
        db_session: Session,
    ):
        # given
        service = JiraSecretService(db_session)

        # when & then
        with pytest.raises(JiraSecretNotFoundException):
            service.get_secret_by_id_or_throw(9999)

    def test_delete_secret(
        self,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        secret = jira_secret_fixture()
        service = JiraSecretService(db_session)

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
        service = JiraSecretService(db_session)

        # when & then
        with pytest.raises(JiraSecretNotFoundException):
            service.delete_secret(9999)

    def test_get_jira_client(
        self,
        mocker,
        db_session: Session,
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        secret = jira_secret_fixture()
        service = JiraSecretService(db_session)

        # mock
        mock_client = MagicMock(spec=JiraClient)
        mocker.patch(
            "dev_blackbox.service.jira_secret_service.get_jira_client",
            return_value=mock_client,
        )

        # when
        result = service.get_jira_client(secret)

        # then
        assert result == mock_client
