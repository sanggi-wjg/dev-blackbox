import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from dev_blackbox.service.command.embedding_command import (
    GeneratePlatformWorkLogEmbeddingCommand,
)
from dev_blackbox.storage.rds.entity.platform_work_log_chunk import PlatformWorkLogChunk
from dev_blackbox.storage.rds.repository import (
    PlatformWorkLogChunkRepository,
)

logger = logging.getLogger(__name__)


class EmbeddingService:

    def __init__(self, session: Session):
        self.platform_work_log_chunk_repository = PlatformWorkLogChunkRepository(session)

    def generate_embedding(
        self,
        commands: list[GeneratePlatformWorkLogEmbeddingCommand],
    ) -> list[PlatformWorkLogChunk]:
        if not commands:
            return []

        command_by_id: dict[int, list[GeneratePlatformWorkLogEmbeddingCommand]] = defaultdict(list)
        for command in commands:
            command_by_id[command.platform_work_log_id].append(command)

        self.platform_work_log_chunk_repository.delete_by_platform_work_log_ids(
            list(command_by_id.keys())
        )

        chunks = []

        for platform_work_log_id, group in command_by_id.items():
            for command in group:
                chunks.append(
                    PlatformWorkLogChunk.create(
                        platform_work_log_id=platform_work_log_id,
                        chunk_index=command.chunk_index,
                        chunk_text=command.chunk_text,
                        embedding=command.embedding,
                    )
                )
        return self.platform_work_log_chunk_repository.save_all(chunks)
