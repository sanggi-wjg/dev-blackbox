from typing import Callable

import pytest
from sqlalchemy.orm import Session

from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.service.command.github_user_secret_command import CreateGitHubUserSecretCommand
from dev_blackbox.core.exception import (
    GitHubUserSecretAlreadyExistException,
    GitHubUserSecretNotFoundException,
    UserNotFoundException,
)
from dev_blackbox.service.github_user_secret_service import GitHubUserSecretService
from dev_blackbox.storage.rds.entity.github_user_secret import GitHubUserSecret
from dev_blackbox.storage.rds.entity.user import User


class GitHubUserSecretServiceTest:

    def test_create_secret(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = GitHubUserSecretService(db_session)
        command = CreateGitHubUserSecretCommand(
            user_id=user.id,
            username="test_user",
            personal_access_token="ghp_test_token_123",
        )
        encrypt_service = get_encrypt_service()

        # when
        result = service.create_secret(command)

        # then
        assert result.user_id == command.user_id
        assert result.username == command.username
        assert (
            encrypt_service.decrypt(result.personal_access_token)
            == command.personal_access_token
        )

    def test_create_secret_존재하지_않는_유저(
        self,
        db_session: Session,
    ):
        # given
        service = GitHubUserSecretService(db_session)
        command = CreateGitHubUserSecretCommand(
            user_id=9999,
            username="test_user",
            personal_access_token="ghp_test_token_123",
        )

        # when & then
        with pytest.raises(UserNotFoundException):
            service.create_secret(command)

    def test_create_secret_이미_시크릿이_존재하면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        github_user_secret_fixture: Callable[..., GitHubUserSecret],
    ):
        # given
        user = user_fixture()
        github_user_secret_fixture(user_id=user.id)
        service = GitHubUserSecretService(db_session)
        command = CreateGitHubUserSecretCommand(
            user_id=user.id,
            username="test_user",
            personal_access_token="ghp_another_token",
        )

        # when & then
        with pytest.raises(GitHubUserSecretAlreadyExistException):
            service.create_secret(command)

    def test_get_secret_by_user_id_or_throw(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        github_user_secret_fixture: Callable[..., GitHubUserSecret],
    ):
        # given
        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)
        service = GitHubUserSecretService(db_session)

        # when
        result = service.get_secret_by_user_id_or_throw(user.id)

        # then
        assert result == secret

    def test_get_secret_by_user_id_or_throw_시크릿이_없으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = GitHubUserSecretService(db_session)

        # when & then
        with pytest.raises(GitHubUserSecretNotFoundException):
            service.get_secret_by_user_id_or_throw(user.id)

    def test_get_decrypted_token_by_secret(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        github_user_secret_fixture: Callable[..., GitHubUserSecret],
    ):
        # given
        user = user_fixture()
        plain_token = "ghp_my_token"
        secret = github_user_secret_fixture(user_id=user.id, personal_access_token=plain_token)
        service = GitHubUserSecretService(db_session)

        # when
        result = service.get_decrypted_token_by_secret(secret)

        # then
        assert result == plain_token

    def test_delete_secret(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        github_user_secret_fixture: Callable[..., GitHubUserSecret],
    ):
        # given
        user = user_fixture()
        github_user_secret_fixture(user_id=user.id)
        service = GitHubUserSecretService(db_session)

        # when
        result = service.delete_secret(user.id)

        # then
        assert result is True
        with pytest.raises(GitHubUserSecretNotFoundException):
            service.get_secret_by_user_id_or_throw(user.id)

    def test_delete_secret_시크릿이_없으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = GitHubUserSecretService(db_session)

        # when & then
        with pytest.raises(GitHubUserSecretNotFoundException):
            service.delete_secret(user.id)
