from sqlalchemy.orm import Session

from dev_blackbox.client.jira_client import get_jira_client
from dev_blackbox.storage.rds.entity.jira_user import JiraUser
from dev_blackbox.storage.rds.repository import JiraUserRepository


class JiraUserService:

    def __init__(self, session: Session):
        self.session = session
        self.jira_user_repository = JiraUserRepository(session)

    def sync_jira_users(self) -> list[JiraUser]:
        jira_client = get_jira_client()
        searched_users = jira_client.fetch_assignable_users(project="FMP")
        searched_account_ids = [user.accountId for user in searched_users]

        jira_users = self.jira_user_repository.find_by_account_ids(searched_account_ids)
        exists_account_ids = {user.account_id for user in jira_users}

        # 새로운 사용자만 저장, 기존 사용자 없애기 X
        new_users = [
            JiraUser.create(
                account_id=user.accountId,
                active=user.active,
                display_name=user.displayName,
                email_address=user.emailAddress,
                url=user.self,
            )
            for user in searched_users
            if user.accountId not in exists_account_ids
        ]

        return self.jira_user_repository.save_all(new_users)
