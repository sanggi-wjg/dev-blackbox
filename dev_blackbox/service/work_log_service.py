from datetime import date

from sqlalchemy.orm import Session

from dev_blackbox.core.cache import cache_evict, cacheable, cache_put
from dev_blackbox.core.const import CacheKey, CacheTTL
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.core.exception import UserContentNotFoundException
from dev_blackbox.service.model.platform_work_log_model import PlatformWorkLogsWithSources
from dev_blackbox.service.query.common_query import OrderDirection
from dev_blackbox.service.query.github_event_query import GitHubEventOrderField
from dev_blackbox.service.query.jira_event_query import JiraEventOrderField
from dev_blackbox.service.query.slack_message_query import SlackMessageOrderField
from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.repository import (
    DailyWorkLogRepository,
    GitHubEventRepository,
    JiraEventRepository,
    PlatformWorkLogRepository,
    SlackMessageRepository,
)


class WorkLogService:

    def __init__(self, session: Session):
        self.platform_work_log_repository = PlatformWorkLogRepository(session)
        self.daily_work_log_repository = DailyWorkLogRepository(session)
        self.github_event_repository = GitHubEventRepository(session)
        self.jira_event_repository = JiraEventRepository(session)
        self.slack_message_repository = SlackMessageRepository(session)

    @cacheable(key=CacheKey.WORK_LOG_PLATFORM, ttl=CacheTTL.MINUTES_15)
    def get_platform_work_logs_with_sources(
        self,
        user_id: int,
        target_date: date,
        platforms: list[PlatformEnum],
    ) -> PlatformWorkLogsWithSources:
        work_logs = (
            self.platform_work_log_repository.find_all_by_user_id_and_target_date_and_platforms(
                user_id, target_date, platforms
            )
        )
        github_events = self.github_event_repository.find_all_by_user_id_and_target_date(
            user_id,
            target_date,
            [(GitHubEventOrderField.ID, OrderDirection.DESC)],
        )
        jira_events = self.jira_event_repository.find_all_by_user_id_and_target_date(
            user_id,
            target_date,
            [(JiraEventOrderField.ID, OrderDirection.DESC)],
        )
        slack_messages = self.slack_message_repository.find_all_by_user_id_and_target_date(
            user_id,
            target_date,
            [(SlackMessageOrderField.ID, OrderDirection.DESC)],
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

    def get_platform_work_logs(
        self,
        user_id: int,
        target_date: date,
        platforms: list[PlatformEnum],
    ) -> list[PlatformWorkLog]:
        return self.platform_work_log_repository.find_all_by_user_id_and_target_date_and_platforms(
            user_id,
            target_date,
            platforms,
        )

    def get_daily_work_log(
        self,
        user_id: int,
        target_date: date,
    ) -> DailyWorkLog | None:
        return self.daily_work_log_repository.find_by_user_id_and_target_date(user_id, target_date)

    def get_daily_work_logs(self, user_id: int) -> list[DailyWorkLog]:
        return self.daily_work_log_repository.find_all_by_user_id(user_id)

    def save_daily_work_log(
        self,
        user_id: int,
        target_date: date,
    ) -> DailyWorkLog:
        # user_content 제외
        platform_work_logs = (
            self.platform_work_log_repository.find_all_by_user_id_and_target_date_and_platforms(
                user_id,
                target_date,
                PlatformEnum.platforms(),
            )
        )
        merged_work_log_text = "\n\n".join(
            work_log.markdown_text for work_log in platform_work_logs
        )
        if not merged_work_log_text:
            merged_work_log_text = ""

        # 기존 일일 요약 삭제 후 새로 저장
        self.daily_work_log_repository.delete_by_user_id_and_target_date(
            user_id=user_id, target_date=target_date
        )
        daily_work_log = DailyWorkLog.create(
            user_id=user_id,
            target_date=target_date,
            content=merged_work_log_text,
        )
        return self.daily_work_log_repository.save(daily_work_log)

    @cacheable(key=CacheKey.WORK_LOG_USER_CONTENT, ttl=CacheTTL.MINUTES_15)
    def get_user_content_or_none(self, user_id: int, target_date: date) -> PlatformWorkLog | None:
        return self.platform_work_log_repository.find_by_user_id_and_target_date_and_platform(
            user_id=user_id,
            target_date=target_date,
            platform=PlatformEnum.USER_CONTENT,
        )

    def create_or_update_user_content(
        self,
        user_id: int,
        target_date: date,
        content: str,
    ) -> tuple[bool, PlatformWorkLog]:
        work_log = self.platform_work_log_repository.find_by_user_id_and_target_date_and_platform(
            user_id=user_id,
            target_date=target_date,
            platform=PlatformEnum.USER_CONTENT,
        )
        if work_log is None:
            return True, self.create_user_content(user_id, target_date, content)
        else:
            return False, self.update_user_content(user_id, target_date, content)

    @cache_put(key=CacheKey.WORK_LOG_USER_CONTENT, ttl=CacheTTL.MINUTES_15)
    def create_user_content(
        self,
        user_id: int,
        target_date: date,
        content: str,
    ) -> PlatformWorkLog:
        return self.platform_work_log_repository.save(
            PlatformWorkLog.create(
                user_id=user_id,
                target_date=target_date,
                platform=PlatformEnum.USER_CONTENT,
                content=content,
                model_name="",
                prompt="",
            )
        )

    @cache_put(key=CacheKey.WORK_LOG_USER_CONTENT, ttl=CacheTTL.MINUTES_15)
    def update_user_content(
        self,
        user_id: int,
        target_date: date,
        new_content: str,
    ) -> PlatformWorkLog:
        work_log = self.platform_work_log_repository.find_by_user_id_and_target_date_and_platform(
            user_id=user_id,
            target_date=target_date,
            platform=PlatformEnum.USER_CONTENT,
        )
        if work_log is None:
            raise UserContentNotFoundException(user_id, target_date)
        return work_log.update_content(new_content)
