import logging

from sqlalchemy.orm import Session

from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import (
    SlackUserNotFoundException,
    SlackUserSecretMismatchException,
    UserNotFoundException,
)
from dev_blackbox.service.slack_secret_service import SlackSecretService
from dev_blackbox.storage.rds.entity.slack_user import SlackUser
from dev_blackbox.storage.rds.repository import SlackUserRepository, UserRepository

logger = logging.getLogger(__name__)


class SlackUserService:

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.slack_user_repository = SlackUserRepository(session)
        self.slack_secret_service = SlackSecretService(session)
        self.encrypt_service = get_encrypt_service()

    def get_slack_users(self, slack_secret_id: int | None = None) -> list[SlackUser]:
        if slack_secret_id is not None:
            return self.slack_user_repository.find_all_by_slack_secret_id(slack_secret_id)
        return self.slack_user_repository.find_all()

    def sync_all_slack_users(self) -> None:
        secrets = self.slack_secret_service.get_secrets()
        for secret in secrets:
            try:
                self.sync_slack_users(secret.id)
                logger.info(f"Synced slack users for secret_id={secret.id}")
            except Exception:
                logger.exception(f"Failed to sync slack users for secret_id={secret.id}")

    def sync_slack_users(self, slack_secret_id: int) -> list[SlackUser]:
        secret = self.slack_secret_service.get_secret_by_id_or_throw(slack_secret_id)
        slack_client = self.slack_secret_service.get_slack_client(secret)

        searched_users = slack_client.fetch_users(filter_bot=True)
        searched_user_ids = [m["id"] for m in searched_users]

        existing_slack_users = self.slack_user_repository.find_by_slack_secret_id_and_member_ids(
            slack_secret_id, searched_user_ids
        )
        exists_user_ids = {u.member_id for u in existing_slack_users}

        new_slack_users: list[SlackUser] = []

        for user in searched_users:
            uid = user["id"]
            if uid in exists_user_ids:
                continue

            is_active = not user.get("deleted", False)
            profile = user.get("profile", {})
            display_name = profile.get("display_name", "")
            real_name = profile.get("real_name", user.get("real_name", ""))
            email = profile.get("email")

            encrypted_display_name = self.encrypt_service.encrypt(display_name)
            encrypted_real_name = self.encrypt_service.encrypt(real_name)
            encrypted_email = self.encrypt_service.encrypt(email) if email else None

            new_slack_users.append(
                SlackUser.create(
                    slack_secret_id=slack_secret_id,
                    member_id=uid,
                    is_active=is_active,
                    display_name=encrypted_display_name,
                    real_name=encrypted_real_name,
                    email=encrypted_email,
                )
            )

        return self.slack_user_repository.save_all(new_slack_users)

    def assign_user(self, user_id: int, slack_secret_id: int, slack_user_id: int) -> SlackUser:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)

        self.slack_secret_service.get_secret_by_id_or_throw(slack_secret_id)

        slack_user = self.slack_user_repository.find_by_id(slack_user_id)
        if slack_user is None:
            raise SlackUserNotFoundException(slack_user_id)

        if slack_user.slack_secret_id != slack_secret_id:
            raise SlackUserSecretMismatchException(slack_user_id, slack_secret_id)

        return slack_user.assign_user(user_id)

    def unassign_user(self, user_id: int, slack_user_id: int) -> SlackUser:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)

        slack_user = self.slack_user_repository.find_by_id(slack_user_id)
        if slack_user is None:
            raise SlackUserNotFoundException(slack_user_id)

        return slack_user.unassign_user()
