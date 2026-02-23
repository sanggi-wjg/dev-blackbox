from sqlalchemy.orm import Session

from dev_blackbox.controller.api.dto.github_user_secret_dto import CreateGitHubSecretRequestDto
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import (
    GitHubUserSecretNotFoundException,
    UserNotFoundException,
    GitHubUserSecretAlreadyExistException,
)
from dev_blackbox.storage.rds.entity.github_user_secret import GitHubUserSecret
from dev_blackbox.storage.rds.repository import GitHubUserSecretRepository, UserRepository


class GitHubUserSecretService:

    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)
        self.github_user_secret_repository = GitHubUserSecretRepository(session)
        self.encrypt_service = get_encrypt_service()

    def create_secret(
        self,
        user_id: int,
        request: CreateGitHubSecretRequestDto,
    ) -> GitHubUserSecret:
        # 권한 등은 유저 부분이 안되었으니 현재는 스킵
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)

        github_user_secret = self.github_user_secret_repository.find_by_user_id(user_id=user.id)
        if github_user_secret:
            raise GitHubUserSecretAlreadyExistException(user_id=user.id)

        encrypted_token = self.encrypt_service.encrypt(request.personal_access_token)
        secret = GitHubUserSecret.create(
            username=request.username,
            personal_access_token=encrypted_token,
            user_id=user.id,
        )
        return self.github_user_secret_repository.save(secret)

    def get_secret_by_user_id_or_throw(self, user_id: int) -> GitHubUserSecret:
        secret = self.github_user_secret_repository.find_by_user_id(user_id)
        if secret is None:
            raise GitHubUserSecretNotFoundException(user_id)
        return secret

    def get_decrypted_token_by_secret(self, secret: GitHubUserSecret) -> str:
        return self.encrypt_service.decrypt(secret.personal_access_token)

    def delete_secret(self, user_id: int) -> bool:
        secret = self.get_secret_by_user_id_or_throw(user_id)
        self.github_user_secret_repository.delete(secret)
        return True
