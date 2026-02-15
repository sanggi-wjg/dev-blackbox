import logging
from datetime import date, timedelta, datetime

from sqlalchemy.orm import Session

from dev_blackbox.client.jira_client import get_jira_client
from dev_blackbox.client.model.jira_model import (
    IssueJQL,
    JiraIssueModel,
    JiraStatusGroup,
)
from dev_blackbox.core.exception import (
    UserByIdNotFoundException,
    JiraUserNotAssignedException,
)
from dev_blackbox.storage.rds.entity.jira_event import JiraEvent
from dev_blackbox.storage.rds.repository import (
    UserRepository,
    JiraUserRepository,
    JiraEventRepository,
)

logger = logging.getLogger(__name__)

MAX_PAGES = 10
PAGE_SIZE = 50


class JiraEventService:

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.jira_user_repository = JiraUserRepository(session)
        self.jira_event_repository = JiraEventRepository(session)

    def get_jira_events(self, user_id: int, target_date: date) -> list[JiraEvent]:
        return self.jira_event_repository.find_all_by_user_id_and_target_date(user_id, target_date)

    def save_jira_events(self, user_id: int, target_date: date | None = None) -> list[JiraEvent]:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserByIdNotFoundException(user_id)

        # target_date가 없으면 유저 타임존 기준 어제 날짜로 설정
        if target_date is None:
            target_date = datetime.now(user.tz_info).date() - timedelta(days=1)

        # JiraUser 조회 (user_id로 매핑된 jira_user)
        jira_users = self.jira_user_repository.find_by_user_id(user_id)
        if not jira_users:
            raise JiraUserNotAssignedException(user_id)

        jira_user = jira_users[0]
        if not jira_user.project:
            logger.warning(
                f"JiraUser에 프로젝트 미할당: jira_user_id={jira_user.id}, user_id={user_id}"
            )
            return []

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

        # Jira API 호출 (페이지네이션)
        jira_client = get_jira_client()
        all_issues: list[JiraIssueModel] = []

        for page in range(MAX_PAGES):
            start_at = page * PAGE_SIZE
            result = jira_client.fetch_search_issues(
                jql=jql,
                start_at=start_at,
                max_results=PAGE_SIZE,
            )
            for issue in result:
                issue_model = JiraIssueModel.from_raw(issue.raw)
                all_issues.append(issue_model)

            if len(result) < PAGE_SIZE:
                break

        logger.info(
            f"Collected {len(all_issues)} Jira issues "
            f"for user_id={user_id}, target_date={target_date}"
        )

        if not all_issues:
            return []

        # Entity 생성 및 저장
        events = []
        for issue_model in all_issues:
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
                    issue_key=issue_model.key,
                    issue=issue_model.model_dump(mode="json"),
                    changelog=changelog_data,
                )
            )

        return self.jira_event_repository.save_all(events)
