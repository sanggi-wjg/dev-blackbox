import logging
from typing import Generator

from dev_blackbox.agent.embedding_agent import get_embedding_agent
from dev_blackbox.core.const import LockKey
from dev_blackbox.core.database import get_db_session
from dev_blackbox.domain.chunker import chunk_content
from dev_blackbox.service.command.embedding_command import (
    GeneratePlatformWorkLogEmbeddingCommand,
)
from dev_blackbox.service.embedding_service import EmbeddingService
from dev_blackbox.service.platform_work_log_service import PlatformWorkLogService
from dev_blackbox.task.context.embedding_context import (
    WorkLogContentContext,
    ChunkedWorkLogContentContext,
)
from dev_blackbox.util.distributed_lock import distributed_lock

logger = logging.getLogger(__name__)


def generate_platform_work_log_embeddings_task():
    with distributed_lock(
        LockKey.GENERATE_PLATFORM_WORK_LOG_EMBEDDINGS_TASK, timeout=600
    ) as acquired:
        if not acquired:
            logger.warning("임베딩 생성 태스크가 이미 실행 중, 건너뜀...")
            return

        with get_db_session() as session:
            work_logs = PlatformWorkLogService(session).get_for_chunk_generation()
            contexts = [WorkLogContentContext.from_entity(work_log) for work_log in work_logs]

        if not contexts:
            return

        chunk_contexts = _create_chunked_content(contexts)
        commands = _create_embedding_commands(chunk_contexts)

        with get_db_session() as session:
            EmbeddingService(session).generate_embedding(commands)


def _create_chunked_content(
    contexts: list[WorkLogContentContext],
) -> Generator[ChunkedWorkLogContentContext, None, None]:
    return (
        ChunkedWorkLogContentContext(
            platform_work_log_id=context.platform_work_log_id,
            chunked_content=chunk_content(
                content=context.content,
                chunk_size=512,
                overlap_size=50,
                split_separator="- ",
            ),
        )
        for context in contexts
    )


def _create_embedding_commands(
    chunk_contexts: Generator[ChunkedWorkLogContentContext, None, None],
) -> list[GeneratePlatformWorkLogEmbeddingCommand]:
    embedding_agent = get_embedding_agent()
    commands: list[GeneratePlatformWorkLogEmbeddingCommand] = []

    for context in chunk_contexts:
        try:
            for chunk_index, chunk_text in enumerate(context.chunked_content):
                commands.append(
                    GeneratePlatformWorkLogEmbeddingCommand(
                        platform_work_log_id=context.platform_work_log_id,
                        chunk_index=chunk_index,
                        chunk_text=chunk_text,
                        embedding=embedding_agent.get_embedding(chunk_text),
                    )
                )
        except Exception as e:
            logger.exception(f"청크 임베딩 생성 실패: {context.platform_work_log_id}, {e}")

    return commands
