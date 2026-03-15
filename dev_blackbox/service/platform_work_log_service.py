from sqlalchemy.orm import Session

from dev_blackbox.core.cache import cache_evict, cacheable
from dev_blackbox.core.const import CacheKey
from dev_blackbox.service.command.platform_work_log_command import SavePlatformWorkLogCommand
from dev_blackbox.service.model.platform_work_log_model import PlatformWorkLogsWithSources
from dev_blackbox.service.query.common_query import OrderDirection
from dev_blackbox.service.query.github_event_query import GitHubEventOrderField
from dev_blackbox.service.query.jira_event_query import JiraEventOrderField
from dev_blackbox.service.query.platform_work_log_query import PlatformWorkLogQuery
from dev_blackbox.service.query.slack_message_query import SlackMessageOrderField
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.repository import (
    GitHubEventRepository,
    JiraEventRepository,
    PlatformWorkLogRepository,
    SlackMessageRepository,
)


class PlatformWorkLogService:

    def __init__(self, session: Session):
        self.platform_work_log_repository = PlatformWorkLogRepository(session)
        self.github_event_repository = GitHubEventRepository(session)
        self.jira_event_repository = JiraEventRepository(session)
        self.slack_message_repository = SlackMessageRepository(session)

    @cacheable(key=CacheKey.WORK_LOG_PLATFORM_QUERY)
    def get_platform_work_logs_with_sources(
        self, query: PlatformWorkLogQuery
    ) -> PlatformWorkLogsWithSources:
        work_logs = self.platform_work_log_repository.find_all_by_user_id_and_target_date(
            query.user_id, query.target_date
        )
        github_events = self.github_event_repository.find_all_by_user_id_and_target_date(
            query.user_id,
            query.target_date,
            [
                (GitHubEventOrderField.ID, OrderDirection.DESC),
            ],
        )
        jira_events = self.jira_event_repository.find_all_by_user_id_and_target_date(
            query.user_id,
            query.target_date,
            [
                (JiraEventOrderField.ID, OrderDirection.DESC),
            ],
        )
        slack_messages = self.slack_message_repository.find_all_by_user_id_and_target_date(
            query.user_id,
            query.target_date,
            [
                (SlackMessageOrderField.ID, OrderDirection.DESC),
            ],
        )
        return PlatformWorkLogsWithSources(
            work_logs=work_logs,
            github_events=github_events,
            jira_events=jira_events,
            slack_messages=slack_messages,
        )

    @cache_evict(key=CacheKey.WORK_LOG_PLATFORM_COMMAND)
    def save_platform_work_log(self, command: SavePlatformWorkLogCommand) -> PlatformWorkLog:
        # 기존 요약 삭제 후 새로 저장
        self.platform_work_log_repository.delete_by_user_id_and_target_date_and_platform(
            user_id=command.user_id,
            target_date=command.target_date,
            platform=command.platform,
        )
        platform_work_log = PlatformWorkLog.create(
            user_id=command.user_id,
            target_date=command.target_date,
            platform=command.platform,
            content=command.content,
            model_name=command.model_name,
            prompt=command.prompt,
            is_empty=command.is_empty,
        )
        return self.platform_work_log_repository.save(platform_work_log)

    def get_for_chunk_generation(self) -> list[PlatformWorkLog]:
        return self.platform_work_log_repository.find_all_without_chunks()
