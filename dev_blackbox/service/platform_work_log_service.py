from datetime import date

from sqlalchemy.orm import Session

from dev_blackbox.core.cache import cache_evict, cacheable
from dev_blackbox.core.const import CacheKey, CacheTTL
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.model.platform_work_log_model import PlatformWorkLogsWithSources
from dev_blackbox.service.query.common_query import OrderDirection
from dev_blackbox.service.query.github_event_query import GitHubEventOrderField
from dev_blackbox.service.query.jira_event_query import JiraEventOrderField
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

    @cacheable(key=CacheKey.WORK_LOG_PLATFORM, ttl=CacheTTL.MINUTES_15)
    def get_platform_work_logs_with_sources(
        self,
        user_id: int,
        target_date: date,
    ) -> PlatformWorkLogsWithSources:
        work_logs = self.platform_work_log_repository.find_all_by_user_id_and_target_date(
            user_id, target_date
        )
        github_events = self.github_event_repository.find_all_by_user_id_and_target_date(
            user_id,
            target_date,
            [
                (GitHubEventOrderField.ID, OrderDirection.DESC),
            ],
        )
        jira_events = self.jira_event_repository.find_all_by_user_id_and_target_date(
            user_id,
            target_date,
            [
                (JiraEventOrderField.ID, OrderDirection.DESC),
            ],
        )
        slack_messages = self.slack_message_repository.find_all_by_user_id_and_target_date(
            user_id,
            target_date,
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

    @cache_evict(key=CacheKey.WORK_LOG_PLATFORM)
    def save_platform_work_log(
        self,
        user_id: int,
        target_date: date,
        platform: PlatformEnum,
        content: str,
        model_name: str,
        prompt: str,
        embedding: list[float] | None = None,
    ) -> PlatformWorkLog:
        # 기존 요약 삭제 후 새로 저장
        self.platform_work_log_repository.delete_by_user_id_and_target_date_and_platform(
            user_id=user_id,
            target_date=target_date,
            platform=platform,
        )
        platform_work_log = PlatformWorkLog.create(
            user_id=user_id,
            target_date=target_date,
            platform=platform,
            content=content,
            model_name=model_name,
            prompt=prompt,
            embedding=embedding,
        )
        return self.platform_work_log_repository.save(platform_work_log)
