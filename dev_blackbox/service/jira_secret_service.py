from sqlalchemy.orm import Session

from dev_blackbox.client.jira_client import JiraClient
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import JiraSecretNotFoundException
from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret
from dev_blackbox.storage.rds.repository import JiraSecretRepository


class JiraSecretService:

    def __init__(self, session: Session):
        self.jira_secret_repository = JiraSecretRepository(session)
        self.encrypt_service = get_encrypt_service()

    def create_secret(
        self,
        name: str,
        url: str,
        username: str,
        api_token: str,
    ) -> JiraSecret:
        encrypted_username = self.encrypt_service.encrypt(username)
        encrypted_api_token = self.encrypt_service.encrypt(api_token)
        secret = JiraSecret.create(
            name=name,
            url=url,
            username=encrypted_username,
            api_token=encrypted_api_token,
        )
        return self.jira_secret_repository.save(secret)

    def get_secrets(self) -> list[JiraSecret]:
        return self.jira_secret_repository.find_all()

    def get_secret_by_id_or_throw(self, jira_secret_id: int) -> JiraSecret:
        secret = self.jira_secret_repository.find_by_id(jira_secret_id)
        if secret is None:
            raise JiraSecretNotFoundException(jira_secret_id)
        return secret

    def delete_secret(self, jira_secret_id: int) -> None:
        secret = self.get_secret_by_id_or_throw(jira_secret_id)
        secret.delete()

    def create_jira_client(self, secret: JiraSecret) -> JiraClient:
        decrypted_username = self.encrypt_service.decrypt(secret.username)
        decrypted_api_token = self.encrypt_service.decrypt(secret.api_token)
        return JiraClient.create(
            server=secret.url,
            username=decrypted_username,
            api_token=decrypted_api_token,
        )
