import logging

from sqlalchemy.orm import Session

from dev_blackbox.client.slack_client import get_slack_client
from dev_blackbox.core.encrypt import get_encrypt_service
from dev_blackbox.core.exception import SlackUserByIdNotFoundException, UserByIdNotFoundException
from dev_blackbox.storage.rds.entity.slack_user import SlackUser
from dev_blackbox.storage.rds.repository import SlackUserRepository, UserRepository

logger = logging.getLogger(__name__)


class SlackUserService:

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.slack_user_repository = SlackUserRepository(session)
        self.encrypt_service = get_encrypt_service()

    def get_slack_users(self) -> list[SlackUser]:
        return self.slack_user_repository.find_all()

    def sync_slack_users(self) -> list[SlackUser]:
        slack_client = get_slack_client()
        searched_users = slack_client.fetch_users(filter_bot=True)
        searched_user_ids: list[str] = [m["id"] for m in searched_users]

        slack_users = self.slack_user_repository.find_by_member_ids(searched_user_ids)
        exists_user_ids = {u.member_id for u in slack_users}

        new_slack_users: list[SlackUser] = []

        # 새로운 사용자만 저장, 기존 사용자 없애기 X
        for user in searched_users:
            uid = user["id"]
            if uid in exists_user_ids:
                continue

            profile = user.get("profile", {})
            display_name = profile.get("display_name", "")
            real_name = profile.get("real_name", user.get("real_name", ""))
            email = profile.get("email")

            encrypted_display_name = self.encrypt_service.encrypt(display_name)
            encrypted_real_name = self.encrypt_service.encrypt(real_name)
            encrypted_email = self.encrypt_service.encrypt(email) if email else None

            new_slack_users.append(
                SlackUser.create(
                    member_id=uid,
                    display_name=encrypted_display_name,
                    real_name=encrypted_real_name,
                    email=encrypted_email,
                )
            )

        return self.slack_user_repository.save_all(new_slack_users)

    def assign_user(self, user_id: int, slack_user_id: int) -> SlackUser:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserByIdNotFoundException(user_id)

        slack_user = self.slack_user_repository.find_by_id(slack_user_id)
        if slack_user is None:
            raise SlackUserByIdNotFoundException(slack_user_id)

        return slack_user.assign_user(user_id)

    def unassign_user(self, user_id: int, slack_user_id: int) -> SlackUser:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserByIdNotFoundException(user_id)

        slack_user = self.slack_user_repository.find_by_id(slack_user_id)
        if slack_user is None:
            raise SlackUserByIdNotFoundException(slack_user_id)

        return slack_user.unassign_user()
