import logging
from datetime import date

from dev_blackbox.agent.llm_agent import LLMAgent
from dev_blackbox.agent.model.llm_model import SummaryOllamaConfig
from dev_blackbox.agent.model.prompt import (
    GITHUB_COMMIT_SUMMARY_PROMPT,
    JIRA_ISSUE_SUMMARY_PROMPT,
    SLACK_MESSAGE_SUMMARY_PROMPT,
)
from dev_blackbox.core.const import EMPTY_ACTIVITY_MESSAGE, LockKey
from dev_blackbox.core.database import get_db_session
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.github_event_service import GitHubEventService
from dev_blackbox.service.jira_event_service import JiraEventService
from dev_blackbox.service.slack_message_service import SlackMessageService
from dev_blackbox.service.user_service import UserService
from dev_blackbox.service.work_log_service import WorkLogService
from dev_blackbox.task.context.user_context import UserContext
from dev_blackbox.util.datetime_util import get_yesterday
from dev_blackbox.util.distributed_lock import distributed_lock

logger = logging.getLogger(__name__)


def collect_events_and_summarize_work_log_task():
    with distributed_lock(
        LockKey.COLLECT_EVENTS_AND_SUMMARIZE_WORK_LOG_TASK.value, timeout=300
    ) as acquired:
        if not acquired:
            logger.warning("collect_platform_task is already running, skipping...")
            return

        with get_db_session() as session:
            user_service = UserService(session)
            users = user_service.get_users()  # fixme n+1
            users_with_related = [UserContext.from_entity(user) for user in users]

        for user in users_with_related:
            _collect_events_and_summarize(user)


def collect_events_and_summarize_work_log_by_user_task(user_id: int, target_date: date):
    lock_key = (
        LockKey.COLLECT_EVENTS_AND_SUMMARIZE_WORK_LOG_TASK.value
        + f":user_id:{user_id}:target_date:{target_date}"
    )
    with distributed_lock(lock_key, timeout=300) as acquired:
        if not acquired:
            logger.warning("collect_platform_task is already running, skipping...")
            return

        with get_db_session() as session:
            user_service = UserService(session)
            user = user_service.get_user_by_id_or_throw(user_id)
            user_model = UserContext.from_entity(user)
        _collect_events_and_summarize(user_model, target_date)


def _collect_events_and_summarize(user: UserContext, target_date: date | None = None):
    target_date = target_date or get_yesterday(user.tz_info)
    _collect_and_summarize(user, target_date)
    _save_daily_work_log(user, target_date)
    logger.info(f"요약 완료: user_id={user.id}, target_date={target_date}")


def _save_daily_work_log(
    user: UserContext,
    target_date: date,
):
    with get_db_session() as session:
        service = WorkLogService(session)
        service.save_daily_work_log(user_id=user.id, target_date=target_date)


def _save_empty_work_log(
    user: UserContext,
    target_date: date,
    platform: PlatformEnum,
    message: str = EMPTY_ACTIVITY_MESSAGE,
):
    with get_db_session() as session:
        service = WorkLogService(session)
        service.save_platform_work_log(
            user_id=user.id,
            target_date=target_date,
            platform=platform,
            content=message,
            model_name="",
            prompt="",
        )


def _collect_and_summarize(user: UserContext, target_date: date):
    # GitHub 데이터셋 수집 + 요약
    try:
        if user.has_github_user_secret:
            commit_message = _collect_github_events(user.id, target_date)
            if commit_message:
                _summarize_github(user, target_date, commit_message)
            else:
                _save_empty_work_log(user, target_date, PlatformEnum.GITHUB)
    except Exception as e:
        logger.exception(
            f"GitHub 데이터 수집/요약 실패: user_id={user.id}, target_date={target_date}, error={e}"
        )

    # Jira 데이터셋 수집 + 요약
    try:
        if user.has_jira_user:
            issue_details = _collect_jira_events(user, target_date)
            if issue_details:
                _summarize_jira(user, target_date, issue_details)
            else:
                _save_empty_work_log(user, target_date, PlatformEnum.JIRA)
    except Exception as e:
        logger.exception(
            f"Jira 데이터 수집/요약 실패: user_id={user.id}, target_date={target_date}, error={e}"
        )

    # Slack 데이터셋 수집 + 요약
    try:
        if user.has_slack_user:
            message_details = _collect_slack_events(user, target_date)
            if message_details:
                _summarize_slack(user, target_date, message_details)
            else:
                _save_empty_work_log(user, target_date, PlatformEnum.SLACK)
    except Exception as e:
        logger.exception(
            f"Slack 데이터 수집/요약 실패: user_id={user.id}, target_date={target_date}, error={e}"
        )


def _collect_github_events(user_id: int, target_date: date) -> str:
    # 모든 이벤트 저장
    with get_db_session() as session:
        service = GitHubEventService(session)
        service.save_github_events(user_id, target_date)

    # 요약 대상 이벤트만 조회
    with get_db_session() as session:
        service = GitHubEventService(session)
        summary_events = service.get_github_events_by_event_types(
            user_id, target_date, GitHubEventService.SUMMARY_EVENT_TYPES
        )
        texts = []
        for event in summary_events:
            if event.commit_model is not None:
                texts.append(event.commit_model.commit_detail_text)
            elif event.event_type == "PullRequestEvent":
                texts.append(event.event_model.pull_request_summary_text)
        summary_text = "\n".join(texts)

    if len(summary_text) > 50000:
        summary_text = summary_text[:50000]
        logger.info(
            f"GitHub 요약 텍스트 길이 제한: user_id={user_id}, target_date={target_date}, text_length={len(summary_text)}"
        )
    return summary_text


def _collect_jira_events(user: UserContext, target_date: date) -> str:
    with get_db_session() as session:
        service = JiraEventService(session)
        events = service.save_jira_events(user.id, target_date)
        issue_details = "\n\n".join(
            e.issue_model.issue_detail_text(target_date, user.tz_info) for e in events
        )

    if len(issue_details) > 50000:
        issue_details = issue_details[:50000]
        logger.info(
            f"Jira 이슈 상세 정보 길이 제한: user_id={user.id}, target_date={target_date}, details_length={len(issue_details)}"
        )
    return issue_details


def _collect_slack_events(user: UserContext, target_date: date) -> str:
    with get_db_session() as session:
        service = SlackMessageService(session)
        messages = service.save_slack_messages(user.id, target_date)
        message_details = "\n".join(f"[#{m.channel_name}] {m.message_text}" for m in messages)

    if len(message_details) > 50000:
        message_details = message_details[:50000]
        logger.info(
            f"Slack 메시지 길이 제한: user_id={user.id}, target_date={target_date}, message_length={len(message_details)}"
        )
    return message_details


def _summarize_github(user: UserContext, target_date: date, commit_message: str):
    llm_config = SummaryOllamaConfig()
    prompt = GITHUB_COMMIT_SUMMARY_PROMPT

    try:
        llm_agent = LLMAgent.create_with_ollama(llm_config)
        summary_text = llm_agent.query(prompt, commit_message=commit_message)
    except Exception:
        logger.exception(f"LLM 요약 실패 (GitHub): user_id={user.id}, target_date={target_date}")
        raise

    with get_db_session() as session:
        service = WorkLogService(session)
        service.save_platform_work_log(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            content=summary_text,
            model_name=llm_config.model,
            prompt=prompt.template,
        )


def _summarize_jira(user: UserContext, target_date: date, issue_details: str):
    llm_config = SummaryOllamaConfig()
    prompt = JIRA_ISSUE_SUMMARY_PROMPT

    try:
        llm_agent = LLMAgent.create_with_ollama(llm_config)
        summary_text = llm_agent.query(prompt, issue_details=issue_details)
    except Exception:
        logger.exception(f"LLM 요약 실패 (Jira): user_id={user.id}, target_date={target_date}")
        raise

    with get_db_session() as session:
        service = WorkLogService(session)
        service.save_platform_work_log(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.JIRA,
            content=summary_text,
            model_name=llm_config.model,
            prompt=prompt.template,
        )


def _summarize_slack(user: UserContext, target_date: date, message_details: str):
    llm_config = SummaryOllamaConfig()
    prompt = SLACK_MESSAGE_SUMMARY_PROMPT

    try:
        llm_agent = LLMAgent.create_with_ollama(llm_config)
        summary_text = llm_agent.query(prompt, message_details=message_details)
    except Exception:
        logger.exception(f"LLM 요약 실패 (Slack): user_id={user.id}, target_date={target_date}")
        raise

    with get_db_session() as session:
        service = WorkLogService(session)
        service.save_platform_work_log(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.SLACK,
            content=summary_text,
            model_name=llm_config.model,
            prompt=prompt.template,
        )
