import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from dev_blackbox.client.model.jira_api_model import (
    IssueJQL,
    JiraIssueModel,
    JiraStatusGroup,
)
from dev_blackbox.core.exception import (
    UserNotFoundException,
    JiraUserNotAssignedException,
    JiraUserProjectNotAssignedException,
)
from dev_blackbox.service.jira_secret_service import JiraSecretService
from dev_blackbox.storage.rds.entity import User
from dev_blackbox.storage.rds.entity.jira_event import JiraEvent
from dev_blackbox.storage.rds.repository import (
    UserRepository,
    JiraEventRepository,
)
from dev_blackbox.util.datetime_util import get_yesterday

logger = logging.getLogger(__name__)


class JiraEventService:

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.jira_event_repository = JiraEventRepository(session)
        self.jira_secret_service = JiraSecretService(session)

    def get_jira_events(
        self,
        user_id: int,
        target_date: date,
    ) -> list[JiraEvent]:
        return self.jira_event_repository.find_all_by_user_id_and_target_date(
            user_id,
            target_date,
        )

    def save_jira_events(
        self,
        user_id: int,
        target_date: date | None = None,
    ) -> list[JiraEvent]:
        user = self._get_user_or_throw(user_id)
        # target_date가 없으면 유저 타임존 기준 어제 날짜로 설정
        target_date = target_date or get_yesterday(user.tz_info)
        jira_user = user.jira_user
        if not jira_user:
            raise JiraUserNotAssignedException(user_id)
        if not jira_user.has_project():
            raise JiraUserProjectNotAssignedException(user_id)
        logger.info(f"Collecting events for user_id={user_id}, target_date={target_date}")

        # 기존 데이터 삭제 후 갱신
        self.jira_event_repository.delete_by_user_id_and_target_date(user_id, target_date)

        # JQL 빌드: target_date 하루 범위
        next_date = target_date + timedelta(days=1)
        jql = IssueJQL(
            project=jira_user.project,
            assignee_account_id=jira_user.account_id,
            include_statuses=JiraStatusGroup.IN_FLIGHT_AND_RESOLVED,
            updated_after=target_date.isoformat(),
            updated_before=next_date.isoformat(),
        )

        jira_client = self.jira_secret_service.get_jira_client(jira_user.jira_secret)
        issues: list[JiraIssueModel] = []

        # Jira API 호출 (페이지네이션 하지 않음, 하루 50개 이상 이슈 업데이트 되는 경우는 드물다고 가정)
        result = jira_client.fetch_search_issues(jql=jql)
        for issue in result:
            issue_model = JiraIssueModel.from_raw(issue.raw)
            issues.append(issue_model)

        logger.info(
            f"Collected {len(issues)} issues for user_id={user_id}, target_date={target_date}"
        )
        if not issues:
            return []

        events = []
        for issue_model in issues:
            # changelog를 target_date 기준으로 필터링하여 저장
            filtered_changelog = issue_model.filter_changelog_by_date(target_date, user.tz_info)
            changelog_data = (
                [h.model_dump(mode="json") for h in filtered_changelog]
                if filtered_changelog
                else None
            )

            events.append(
                JiraEvent.create(
                    user_id=user_id,
                    jira_user_id=jira_user.id,
                    target_date=target_date,
                    issue_id=issue_model.id,
                    issue_key=issue_model.key,
                    issue=issue_model.model_dump(mode="json"),
                    changelog=changelog_data,
                )
            )

        return self.jira_event_repository.save_all(events)

    def _get_user_or_throw(self, user_id: int) -> User:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)
        return user
