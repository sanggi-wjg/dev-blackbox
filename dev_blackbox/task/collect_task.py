from dev_blackbox.agent.llm_agent import LLMAgent
from dev_blackbox.agent.model.llm_model import SummaryOllamaConfig
from dev_blackbox.agent.model.prompt import GITHUB_COMMIT_SUMMARY_PROMPT
from dev_blackbox.core.database import get_db_session
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.github_collect_service import GitHubCollectService


def collect_by_platform_task(platform: PlatformEnum, user_id: int):
    if not platform:
        raise ValueError("platform must be provided.")

    if platform == PlatformEnum.GITHUB:
        with get_db_session() as session:
            github_collect_service = GitHubCollectService(session)
            results = github_collect_service.collect_yesterday_commit_info(user_id)

        llm_agent = LLMAgent.create_with_ollama(SummaryOllamaConfig())
        summary = llm_agent.query(GITHUB_COMMIT_SUMMARY_PROMPT, commit_message="\n".join(results))
