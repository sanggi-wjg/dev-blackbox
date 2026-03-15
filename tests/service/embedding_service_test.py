from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.command.embedding_command import (
    GeneratePlatformWorkLogEmbeddingCommand,
)
from dev_blackbox.service.embedding_service import EmbeddingService
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.platform_work_log_chunk import PlatformWorkLogChunk
from dev_blackbox.storage.rds.entity.user import User
from dev_blackbox.storage.rds.repository import PlatformWorkLogChunkRepository


class EmbeddingServiceTest:

    def test_generate_embedding(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        work_log = platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 6, 1),
            platform=PlatformEnum.GITHUB,
            content="테스트 요약",
        )
        fake_embedding = [0.1] * 1024
        commands = [
            GeneratePlatformWorkLogEmbeddingCommand(
                platform_work_log_id=work_log.id,
                chunk_index=0,
                chunk_text="테스트 요약",
                embedding=fake_embedding,
            )
        ]
        service = EmbeddingService(db_session)

        # when
        service.generate_embedding(commands)

        # then
        db_session.flush()
        chunks = PlatformWorkLogChunkRepository(db_session).find_all_by_ids(
            [
                c.id
                for c in db_session.query(PlatformWorkLogChunk)
                .filter(PlatformWorkLogChunk.platform_work_log_id == work_log.id)
                .all()
            ]
        )
        assert len(chunks) == 1
        assert chunks[0].chunk_text == "테스트 요약"
        assert chunks[0].embedding is not None
        assert list(chunks[0].embedding) == fake_embedding

    def test_generate_embedding_여러_work_log(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        work_log_1 = platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 6, 1),
            platform=PlatformEnum.GITHUB,
            content="GitHub 요약",
        )
        work_log_2 = platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 6, 1),
            platform=PlatformEnum.JIRA,
            content="Jira 요약",
        )
        embedding_1 = [0.1] * 1024
        embedding_2 = [0.2] * 1024
        commands = [
            GeneratePlatformWorkLogEmbeddingCommand(
                platform_work_log_id=work_log_1.id,
                chunk_index=0,
                chunk_text="GitHub 청크",
                embedding=embedding_1,
            ),
            GeneratePlatformWorkLogEmbeddingCommand(
                platform_work_log_id=work_log_2.id,
                chunk_index=0,
                chunk_text="Jira 청크",
                embedding=embedding_2,
            ),
        ]
        service = EmbeddingService(db_session)

        # when
        service.generate_embedding(commands)

        # then
        db_session.flush()
        all_chunks = (
            db_session.query(PlatformWorkLogChunk)
            .filter(PlatformWorkLogChunk.platform_work_log_id.in_([work_log_1.id, work_log_2.id]))
            .all()
        )
        assert len(all_chunks) == 2
        chunk_map = {c.platform_work_log_id: c for c in all_chunks}
        chunk_1 = chunk_map[work_log_1.id]
        chunk_2 = chunk_map[work_log_2.id]
        assert chunk_1.embedding is not None
        assert list(chunk_1.embedding) == embedding_1
        assert chunk_2.embedding is not None
        assert list(chunk_2.embedding) == embedding_2

    def test_generate_embedding_같은_work_log의_여러_청크(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        work_log = platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 6, 2),
            platform=PlatformEnum.GITHUB,
            content="긴 요약",
        )
        embedding_0 = [0.1] * 1024
        embedding_1 = [0.2] * 1024
        commands = [
            GeneratePlatformWorkLogEmbeddingCommand(
                platform_work_log_id=work_log.id,
                chunk_index=0,
                chunk_text="첫 번째 청크",
                embedding=embedding_0,
            ),
            GeneratePlatformWorkLogEmbeddingCommand(
                platform_work_log_id=work_log.id,
                chunk_index=1,
                chunk_text="두 번째 청크",
                embedding=embedding_1,
            ),
        ]
        service = EmbeddingService(db_session)

        # when
        service.generate_embedding(commands)

        # then
        db_session.flush()
        chunks = (
            db_session.query(PlatformWorkLogChunk)
            .filter(PlatformWorkLogChunk.platform_work_log_id == work_log.id)
            .order_by(PlatformWorkLogChunk.chunk_index)
            .all()
        )
        assert len(chunks) == 2
        assert chunks[0].chunk_index == 0
        assert chunks[0].chunk_text == "첫 번째 청크"
        assert chunks[0].embedding is not None
        assert list(chunks[0].embedding) == embedding_0
        assert chunks[1].chunk_index == 1
        assert chunks[1].chunk_text == "두 번째 청크"
        assert chunks[1].embedding is not None
        assert list(chunks[1].embedding) == embedding_1

    def test_generate_embedding_기존_청크_교체(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given — 기존 청크가 있는 상태
        user = user_fixture()
        work_log = platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 6, 3),
            platform=PlatformEnum.GITHUB,
            content="요약",
        )
        old_chunk = PlatformWorkLogChunk.create(
            platform_work_log_id=work_log.id,
            chunk_index=0,
            chunk_text="이전 청크",
            embedding=[0.5] * 1024,
        )
        db_session.add(old_chunk)
        db_session.flush()
        old_chunk_id = old_chunk.id

        # 새 커맨드
        new_embedding = [0.9] * 1024
        commands = [
            GeneratePlatformWorkLogEmbeddingCommand(
                platform_work_log_id=work_log.id,
                chunk_index=0,
                chunk_text="새 청크",
                embedding=new_embedding,
            ),
        ]
        service = EmbeddingService(db_session)

        # when
        service.generate_embedding(commands)

        # then — 기존 청크 삭제, 새 청크 저장
        db_session.flush()
        chunks = (
            db_session.query(PlatformWorkLogChunk)
            .filter(PlatformWorkLogChunk.platform_work_log_id == work_log.id)
            .all()
        )
        assert len(chunks) == 1
        assert chunks[0].id != old_chunk_id
        assert chunks[0].chunk_text == "새 청크"
        assert chunks[0].embedding is not None
        assert list(chunks[0].embedding) == new_embedding

    def test_generate_embedding_빈_커맨드(
        self,
        db_session: Session,
    ):
        # given
        service = EmbeddingService(db_session)

        # when / then — 에러 없이 완료
        service.generate_embedding([])
