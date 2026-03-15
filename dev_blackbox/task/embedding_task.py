import logging

from dev_blackbox.agent.embedding_agent import get_embedding_agent
from dev_blackbox.core.const import LockKey
from dev_blackbox.core.database import get_db_session
from dev_blackbox.service.command.embedding_command import UpdatePlatformWorkLogEmbeddingCommand
from dev_blackbox.service.embedding_service import EmbeddingService
from dev_blackbox.service.platform_work_log_service import PlatformWorkLogService
from dev_blackbox.task.context.embedding_context import EmbeddingContext
from dev_blackbox.util.distributed_lock import distributed_lock

logger = logging.getLogger(__name__)


def generate_embeddings_task():
    with distributed_lock(LockKey.GENERATE_EMBEDDINGS_TASK, timeout=600) as acquired:
        if not acquired:
            logger.warning("임베딩 생성 태스크가 이미 실행 중, 건너뜀...")
            return

        with get_db_session() as session:
            service = PlatformWorkLogService(session)
            work_logs = service.get_for_embedding_generation()
            contexts = [EmbeddingContext.from_platform_work_log(work_log) for work_log in work_logs]

        embedding_agent = get_embedding_agent()
        commands = []

        for context in contexts:
            try:
                commands.append(
                    UpdatePlatformWorkLogEmbeddingCommand(
                        work_log_id=context.work_log_id,
                        embedding=embedding_agent.get_embedding(context.content),
                    )
                )
            except Exception as e:
                logger.warning(f"임베딩 생성 실패: {context.work_log_id}, {e}")

        with get_db_session() as session:
            service = EmbeddingService(session)
            service.update_embedding(commands)
