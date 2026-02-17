import logging
from datetime import date

from dev_blackbox.agent.llm_agent import LLMAgent
from dev_blackbox.agent.model.llm_model import SummaryOllamaConfig
from dev_blackbox.agent.model.prompt import (
    GITHUB_COMMIT_SUMMARY_PROMPT,
    JIRA_ISSUE_SUMMARY_PROMPT,
    SLACK_MESSAGE_SUMMARY_PROMPT,
)
from dev_blackbox.core.database import get_db_session
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.github_event_service import GitHubEventService
from dev_blackbox.service.jira_event_service import JiraEventService
from dev_blackbox.service.slack_message_service import SlackMessageService
from dev_blackbox.service.model.user_model import UserWithRelated
from dev_blackbox.service.summary_service import SummaryService
from dev_blackbox.service.user_service import UserService
from dev_blackbox.util.datetime_util import get_yesterday
from dev_blackbox.util.distributed_lock import DistributedLockName, distributed_lock

logger = logging.getLogger(__name__)


def collect_platform_task():
    # todo 각 플랫폼별로 user_id 리스트를 가져와서 반복적으로 수집하도록 변경 필요
    # 아직 미구현이 많아서 코드 정리는 어느정도 이후 진행하자.
    with distributed_lock(DistributedLockName.COLLECT_PLATFORM_TASK, timeout=300) as acquired:
        if not acquired:
            logger.warning("collect_platform_task is already running, skipping...")
            return

        with get_db_session() as session:
            user_service = UserService(session)
            users = user_service.get_users()  # fixme n+1
            users_with_related = [UserWithRelated.from_entity(user) for user in users]

        for user in users_with_related:
            target_date = get_yesterday(user.tz_info)
            try:
                _collect_and_summary(user, target_date)
                logger.info(f"요약 완료: user_id={user.id}, target_date={target_date}")
            except Exception:
                logger.exception(f"요약 실패: user_id={user.id}, target_date={target_date}")

            # 통합 일일 요약 저장 (현재 단일 플랫폼이므로 주석 처리)
            # with get_db_session() as session:
            #     summary_service = SummaryService(session)
            #     summary_service.save_daily_summary(
            #         user_id=user_id,
            #         target_date=target_date,
            #         summary=summary_text,
            #         model_name=config.model,
            #         prompt=prompt_text,
            #     )


def _collect_and_summary(user: UserWithRelated, target_date: date):
    # GitHub 데이터셋 수집 + 요약
    if user.github_user_secret is not None:
        commit_message = _collect_github_dataset(user.id, target_date)
        if commit_message:
            _summarize_github(user, target_date, commit_message)
        else:
            logger.info(f"커밋 데이터 없음: user_id={user.id}, target_date={target_date}")
    else:
        logger.info(f"GitHubUser 미할당, GitHub 수집 건너뜀: user_id={user.id}")

    # Jira 데이터셋 수집 + 요약
    if user.jira_user is not None:
        issue_details = _collect_jira_dataset(user, target_date)
        if issue_details:
            _summarize_jira(user, target_date, issue_details)
        else:
            logger.info(f"Jira 이슈 데이터 없음: user_id={user.id}, target_date={target_date}")
    else:
        logger.info(f"JiraUser 미할당, Jira 수집 건너뜀: user_id={user.id}")

    # Slack 데이터셋 수집 + 요약
    if user.slack_user is not None:
        message_details = _collect_slack_dataset(user, target_date)
        if message_details:
            _summarize_slack(user, target_date, message_details)
        else:
            logger.info(f"Slack 메시지 데이터 없음: user_id={user.id}, target_date={target_date}")
    else:
        logger.info(f"SlackUser 미할당, Slack 수집 건너뜀: user_id={user.id}")


def _collect_github_dataset(user_id: int, target_date: date) -> str:
    with get_db_session() as session:
        service = GitHubEventService(session)
        events = service.save_github_events(user_id, target_date)
        commit_message = "\n".join(
            [e.commit_model.commit_detail_text for e in events if e.commit_model is not None]
        )
    return commit_message


def _collect_jira_dataset(user: UserWithRelated, target_date: date) -> str:
    with get_db_session() as session:
        service = JiraEventService(session)
        events = service.save_jira_events(user.id, target_date)
        issue_details = "\n\n".join(
            e.issue_model.issue_detail_text(target_date, user.tz_info) for e in events
        )
    return issue_details


def _summarize_github(user: UserWithRelated, target_date: date, commit_message: str):
    llm_config = SummaryOllamaConfig()
    prompt = GITHUB_COMMIT_SUMMARY_PROMPT

    try:
        llm_agent = LLMAgent.create_with_ollama(llm_config)
        summary_text = llm_agent.query(prompt, commit_message=commit_message)
    except Exception:
        logger.exception(f"LLM 요약 실패 (GitHub): user_id={user.id}, target_date={target_date}")
        raise

    with get_db_session() as session:
        summary_service = SummaryService(session)
        summary_service.save_platform_summary(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            summary=summary_text,
            model_name=llm_config.model,
            prompt=prompt.template,
        )


def _collect_slack_dataset(user: UserWithRelated, target_date: date) -> str:
    with get_db_session() as session:
        service = SlackMessageService(session)
        messages = service.save_slack_messages(user.id, target_date)
        message_details = "\n".join(f"[#{m.channel_name}] {m.message_text}" for m in messages)
    # LLM context 초과 방지
    if len(message_details) > 50000:
        message_details = message_details[:50000]
    return message_details


def _summarize_slack(user: UserWithRelated, target_date: date, message_details: str):
    llm_config = SummaryOllamaConfig()
    prompt = SLACK_MESSAGE_SUMMARY_PROMPT

    try:
        llm_agent = LLMAgent.create_with_ollama(llm_config)
        summary_text = llm_agent.query(prompt, message_details=message_details)
    except Exception:
        logger.exception(f"LLM 요약 실패 (Slack): user_id={user.id}, target_date={target_date}")
        raise

    with get_db_session() as session:
        summary_service = SummaryService(session)
        summary_service.save_platform_summary(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.SLACK,
            summary=summary_text,
            model_name=llm_config.model,
            prompt=prompt.template,
        )


def _summarize_jira(user: UserWithRelated, target_date: date, issue_details: str):
    llm_config = SummaryOllamaConfig()
    prompt = JIRA_ISSUE_SUMMARY_PROMPT

    try:
        llm_agent = LLMAgent.create_with_ollama(llm_config)
        summary_text = llm_agent.query(prompt, issue_details=issue_details)
    except Exception:
        logger.exception(f"LLM 요약 실패 (Jira): user_id={user.id}, target_date={target_date}")
        raise

    with get_db_session() as session:
        summary_service = SummaryService(session)
        summary_service.save_platform_summary(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.JIRA,
            summary=summary_text,
            model_name=llm_config.model,
            prompt=prompt.template,
        )
