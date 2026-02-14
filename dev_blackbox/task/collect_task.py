import logging

from dev_blackbox.core.database import get_db_session
from dev_blackbox.service.github_collect_service import GitHubCollectService

logger = logging.getLogger(__name__)


def collect_platform_task():
    # todo get users
    user_id = 1

    with get_db_session() as session:
        github_collect_service = GitHubCollectService(session)
        github_collect_service.collect_github_events(user_id)

    # llm_agent = LLMAgent.create_with_ollama(SummaryOllamaConfig())
    # summary = llm_agent.query(GITHUB_COMMIT_SUMMARY_PROMPT, commit_message="\n".join(results))
