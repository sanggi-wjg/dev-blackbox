from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.command.platform_work_log_command import SavePlatformWorkLogCommand
from dev_blackbox.service.platform_work_log_service import PlatformWorkLogService
from dev_blackbox.service.query.platform_work_log_query import PlatformWorkLogQuery
from dev_blackbox.storage.rds.entity.github_event import GitHubEvent
from dev_blackbox.storage.rds.entity.github_user_secret import GitHubUserSecret
from dev_blackbox.storage.rds.entity.jira_event import JiraEvent
from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret
from dev_blackbox.storage.rds.entity.jira_user import JiraUser
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.platform_work_log_chunk import PlatformWorkLogChunk
from dev_blackbox.storage.rds.entity.slack_message import SlackMessage
from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret
from dev_blackbox.storage.rds.entity.slack_user import SlackUser
from dev_blackbox.storage.rds.entity.user import User


class PlatformWorkLogServiceTest:

    # ── save_platform_work_log ──

    def test_save_platform_work_log(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        service = PlatformWorkLogService(db_session)

        # when
        command = SavePlatformWorkLogCommand(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            content="GitHub summary",
            model_name="llama3",
            prompt="Summarize commits",
            is_empty=False,
        )
        result = service.save_platform_work_log(command)

        # then
        assert result.user_id == user.id
        assert result.platform == PlatformEnum.GITHUB
        assert result.content == "GitHub summary"

    # ── get_platform_work_logs_with_sources ──

    def test_get_platform_work_logs_with_sources(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        github_user_secret_fixture: Callable[..., GitHubUserSecret],
        github_event_fixture: Callable[..., GitHubEvent],
        jira_secret_fixture: Callable[..., JiraSecret],
        jira_user_fixture: Callable[..., JiraUser],
        jira_event_fixture: Callable[..., JiraEvent],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
        slack_message_fixture: Callable[..., SlackMessage],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture("worklog-sources@dev.com")
        target_date = date(2025, 1, 1)

        github_secret = github_user_secret_fixture(user_id=user.id)
        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=github_secret.id,
            target_date=target_date,
        )

        jira_secret = jira_secret_fixture()
        jira_user = jira_user_fixture(jira_secret_id=jira_secret.id, user_id=user.id)
        jira_event_fixture(user_id=user.id, jira_user_id=jira_user.id, target_date=target_date)

        slack_secret = slack_secret_fixture()
        slack_user = slack_user_fixture(slack_secret_id=slack_secret.id, user_id=user.id)
        slack_message_fixture(user_id=user.id, slack_user_id=slack_user.id, target_date=target_date)

        platform_work_log_fixture(user_id=user.id, target_date=target_date)

        service = PlatformWorkLogService(db_session)
        query = PlatformWorkLogQuery(user_id=user.id, target_date=target_date)

        # when
        result = service.get_platform_work_logs_with_sources(query)

        # then
        assert len(result.work_logs) == 1
        assert len(result.github_events) == 1
        assert len(result.jira_events) == 1
        assert len(result.slack_messages) == 1

    def test_get_platform_work_logs_with_sources_데이터_없으면_빈_리스트(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture("worklog-empty@dev.com")
        service = PlatformWorkLogService(db_session)
        query = PlatformWorkLogQuery(user_id=user.id, target_date=date(2025, 1, 1))

        # when
        result = service.get_platform_work_logs_with_sources(query)

        # then
        assert result.work_logs == []
        assert result.github_events == []
        assert result.jira_events == []
        assert result.slack_messages == []

    # ── get_for_chunk_generation ──

    def test_get_for_chunk_generation(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture("chunk-gen@dev.com")
        work_log = platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 2, 1),
            content="청크 생성 대상 콘텐츠",
        )
        service = PlatformWorkLogService(db_session)

        # when
        result = service.get_for_chunk_generation()

        # then
        assert work_log in result

    def test_get_for_chunk_generation_청크가_있으면_제외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
        platform_work_log_chunk_fixture: Callable[..., PlatformWorkLogChunk],
    ):
        # given
        user = user_fixture("chunk-gen-exclude@dev.com")
        work_log = platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 2, 2),
            content="이미 청크가 있는 콘텐츠",
        )
        platform_work_log_chunk_fixture(platform_work_log_id=work_log.id)
        service = PlatformWorkLogService(db_session)

        # when
        result = service.get_for_chunk_generation()

        # then
        assert work_log not in result

    def test_get_for_chunk_generation_빈_콘텐츠_제외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture("chunk-gen-empty@dev.com")
        empty_log = platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 2, 3),
            content="",
        )
        is_empty_log = platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 2, 3),
            platform=PlatformEnum.JIRA,
            content="빈 활동",
            is_empty=True,
        )
        service = PlatformWorkLogService(db_session)

        # when
        result = service.get_for_chunk_generation()

        # then
        assert empty_log not in result
        assert is_empty_log not in result
