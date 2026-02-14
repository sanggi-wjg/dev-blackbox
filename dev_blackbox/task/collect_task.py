import logging
from datetime import timedelta, datetime, date

from dev_blackbox.agent.llm_agent import LLMAgent
from dev_blackbox.agent.model.llm_model import SummaryOllamaConfig
from dev_blackbox.agent.model.prompt import GITHUB_COMMIT_SUMMARY_PROMPT
from dev_blackbox.core.database import get_db_session
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.github_collect_service import GitHubCollectService
from dev_blackbox.service.summary_service import SummaryService
from dev_blackbox.service.user_service import UserService

logger = logging.getLogger(__name__)


def _collect_github_dataset(user_id: int, target_date: date) -> str:
    with get_db_session() as session:
        service = GitHubCollectService(session)
        events = service.save_github_events(user_id, target_date)
        commit_message = "\n".join(
            [e.commit_model.commit_detail_text for e in events if e.commit_model is not None]
        )
    return commit_message


def collect_platform_task():
    # todo 각 플랫폼별로 user_id 리스트를 가져와서 반복적으로 수집하도록 변경 필요
    # 아직 미구현이 많아서 코드 정리는 어느정도 이후 진행하자.
    user_id = 1

    with get_db_session() as session:
        user_service = UserService(session)
        user = user_service.get_user(user_id)
        target_date = datetime.now(user.tz_info).date() - timedelta(days=1)

    # 데이터셋 수집
    commit_message = _collect_github_dataset(user_id, target_date)

    if not commit_message:
        logger.warning(f"커밋 데이터 없음: user_id={user_id}, target_date={target_date}")
        return

    # LLM 요약
    llm_config = SummaryOllamaConfig()
    prompt = GITHUB_COMMIT_SUMMARY_PROMPT

    try:
        llm_agent = LLMAgent.create_with_ollama(llm_config)
        summary_text = llm_agent.query(prompt, commit_message=commit_message)
    except Exception:
        logger.exception(f"LLM 요약 실패: user_id={user_id}, target_date={target_date}")
        raise

    # 플랫폼 요약 저장
    with get_db_session() as session:
        summary_service = SummaryService(session)
        summary_service.save_platform_summary(
            user_id=user_id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            summary=summary_text,
            model_name=llm_config.model,
            prompt=prompt.template,  # format 하면 너무 커져서 템플릿만
        )

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

    logger.info(f"요약 완료: user_id={user_id}, target_date={target_date}")
