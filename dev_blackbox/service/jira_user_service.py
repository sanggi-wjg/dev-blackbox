import logging

from sqlalchemy.orm import Session

from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import (
    JiraUserNotFoundException,
    JiraUserSecretMismatchException,
    UserNotFoundException,
)
from dev_blackbox.service.jira_secret_service import JiraSecretService
from dev_blackbox.storage.rds.entity.jira_user import JiraUser
from dev_blackbox.storage.rds.repository import JiraUserRepository, UserRepository

logger = logging.getLogger(__name__)


class JiraUserService:

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.jira_user_repository = JiraUserRepository(session)
        self.jira_secret_service = JiraSecretService(session)
        self.encrypt_service = get_encrypt_service()

    def get_jira_users(self, jira_secret_id: int | None = None) -> list[JiraUser]:
        if jira_secret_id is not None:
            return self.jira_user_repository.find_all_by_jira_secret_id(jira_secret_id)
        return self.jira_user_repository.find_all()

    def sync_all_jira_users(self) -> None:
        secrets = self.jira_secret_service.get_secrets()
        for secret in secrets:
            jira_users = self.jira_user_repository.find_all_by_jira_secret_id(secret.id)
            projects = {u.project for u in jira_users if u.project}
            if not projects:
                logger.info(f"No projects found for secret_id={secret.id}, skipping sync")
                continue

            for project in projects:
                try:
                    self.sync_jira_users(secret.id, project)
                    logger.info(f"Synced jira users for secret_id={secret.id}, project={project}")
                except Exception:
                    logger.exception(
                        f"Failed to sync jira users for secret_id={secret.id}, project={project}"
                    )

    def sync_jira_users(self, jira_secret_id: int, project: str) -> list[JiraUser]:
        secret = self.jira_secret_service.get_secret_by_id_or_throw(jira_secret_id)
        jira_client = self.jira_secret_service.get_jira_client(secret)

        searched_users = jira_client.fetch_assignable_users(project=project)
        searched_account_ids = [user.accountId for user in searched_users]

        existing_jira_users = self.jira_user_repository.find_by_jira_secret_id_and_account_ids(
            jira_secret_id, searched_account_ids
        )
        exists_account_ids = {user.account_id for user in existing_jira_users}

        new_users: list[JiraUser] = []
        for user in searched_users:
            if user.accountId in exists_account_ids:
                continue

            encrypted_display_name = self.encrypt_service.encrypt(user.displayName)
            encrypted_email_address = self.encrypt_service.encrypt(user.emailAddress)

            new_users.append(
                JiraUser.create(
                    jira_secret_id=jira_secret_id,
                    account_id=user.accountId,
                    is_active=user.active,
                    display_name=encrypted_display_name,
                    email_address=encrypted_email_address,
                    url=user.self,
                )
            )

        return self.jira_user_repository.save_all(new_users)

    def assign_user(
        self, user_id: int, jira_secret_id: int, jira_user_id: int, project: str
    ) -> JiraUser:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)

        self.jira_secret_service.get_secret_by_id_or_throw(jira_secret_id)

        jira_user = self.jira_user_repository.find_by_id(jira_user_id)
        if jira_user is None:
            raise JiraUserNotFoundException(jira_user_id)

        if jira_user.jira_secret_id != jira_secret_id:
            raise JiraUserSecretMismatchException(jira_user_id, jira_secret_id)

        return jira_user.assign_user_and_project(user_id, project)

    def unassign_user(self, user_id: int, jira_user_id: int) -> JiraUser:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)

        jira_user = self.jira_user_repository.find_by_id(jira_user_id)
        if jira_user is None:
            raise JiraUserNotFoundException(jira_user_id)

        return jira_user.unassign_user()
