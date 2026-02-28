from sqlalchemy.orm import Session

from dev_blackbox.client.slack_client import SlackClient, get_slack_client
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import SlackSecretNotFoundException
from dev_blackbox.service.command.slack_secret_command import CreateSlackSecretCommand
from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret
from dev_blackbox.storage.rds.repository import SlackSecretRepository


class SlackSecretService:

    def __init__(self, session: Session):
        self.slack_secret_repository = SlackSecretRepository(session)
        self.encrypt_service = get_encrypt_service()

    def create_secret(self, command: CreateSlackSecretCommand) -> SlackSecret:
        encrypted_bot_token = self.encrypt_service.encrypt(command.bot_token)
        secret = SlackSecret.create(
            name=command.name,
            bot_token=encrypted_bot_token,
        )
        return self.slack_secret_repository.save(secret)

    def get_secrets(self) -> list[SlackSecret]:
        return self.slack_secret_repository.find_all()

    def get_secret_by_id_or_throw(self, slack_secret_id: int) -> SlackSecret:
        secret = self.slack_secret_repository.find_by_id(slack_secret_id)
        if secret is None:
            raise SlackSecretNotFoundException(slack_secret_id)
        return secret

    def delete_secret(self, slack_secret_id: int) -> None:
        secret = self.get_secret_by_id_or_throw(slack_secret_id)
        secret.delete()

    def get_slack_client(self, secret: SlackSecret) -> SlackClient:
        decrypted_bot_token = self.encrypt_service.decrypt(secret.bot_token)
        return get_slack_client(bot_token=decrypted_bot_token)
