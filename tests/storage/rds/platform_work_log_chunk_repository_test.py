from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.platform_work_log_chunk import PlatformWorkLogChunk
from dev_blackbox.storage.rds.entity.user import User
from dev_blackbox.storage.rds.repository import PlatformWorkLogChunkRepository


class PlatformWorkLogChunkRepositoryTest:

    def test_save_all(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        work_log = platform_work_log_fixture(user_id=user.id)
        chunks = [
            PlatformWorkLogChunk.create(
                platform_work_log_id=work_log.id,
                chunk_index=0,
                chunk_text="첫 번째 청크",
            ),
            PlatformWorkLogChunk.create(
                platform_work_log_id=work_log.id,
                chunk_index=1,
                chunk_text="두 번째 청크",
            ),
        ]
        repository = PlatformWorkLogChunkRepository(db_session)

        # when
        saved = repository.save_all(chunks)

        # then
        assert len(saved) == 2
        assert all(chunk.id is not None for chunk in saved)

    def test_find_all_with_null_embedding(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        work_log = platform_work_log_fixture(user_id=user.id)
        chunk_with_embedding = PlatformWorkLogChunk.create(
            platform_work_log_id=work_log.id,
            chunk_index=0,
            chunk_text="임베딩 있는 청크",
        )
        chunk_with_embedding.update_embedding([0.1] * 1024)
        chunk_without_embedding = PlatformWorkLogChunk.create(
            platform_work_log_id=work_log.id,
            chunk_index=1,
            chunk_text="임베딩 없는 청크",
        )
        empty_chunk = PlatformWorkLogChunk.create(
            platform_work_log_id=work_log.id,
            chunk_index=2,
            chunk_text="",
        )
        db_session.add_all([chunk_with_embedding, chunk_without_embedding, empty_chunk])
        db_session.flush()

        repository = PlatformWorkLogChunkRepository(db_session)

        # when
        results = repository.find_all_with_null_embedding()

        # then — 임베딩 없고 빈 텍스트가 아닌 청크만 반환
        assert len(results) == 1
        assert results[0].chunk_text == "임베딩 없는 청크"

    def test_find_similar_by_embedding(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        work_log = platform_work_log_fixture(user_id=user.id)
        embedding_a = [1.0] + [0.0] * 1023
        embedding_b = [0.0] + [1.0] + [0.0] * 1022

        chunk_a = PlatformWorkLogChunk.create(
            platform_work_log_id=work_log.id,
            chunk_index=0,
            chunk_text="인증 관련 청크",
        )
        chunk_a.update_embedding(embedding_a)

        chunk_b = PlatformWorkLogChunk.create(
            platform_work_log_id=work_log.id,
            chunk_index=1,
            chunk_text="배포 관련 청크",
        )
        chunk_b.update_embedding(embedding_b)

        db_session.add_all([chunk_a, chunk_b])
        db_session.flush()

        repository = PlatformWorkLogChunkRepository(db_session)

        # when — embedding_a와 동일한 벡터로 검색
        results = repository.find_similar_by_embedding(
            user_id=user.id,
            query_embedding=embedding_a,
            similarity=2.0,
            limit=10,
        )

        # then — 가장 유사한 결과가 먼저 반환
        assert len(results) == 2
        assert results[0].platform_work_log_chunk.chunk_text == "인증 관련 청크"
        assert results[0].distance < results[1].distance

    def test_find_similar_by_embedding_다른_유저_제외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user_a = user_fixture("chunk_usera@dev.com")
        user_b = user_fixture("chunk_userb@dev.com")
        embedding = [1.0] + [0.0] * 1023

        log_a = PlatformWorkLog.create(
            user_id=user_a.id,
            target_date=date(2025, 8, 1),
            platform=PlatformEnum.GITHUB,
            content="A 작업",
            model_name="test-model",
            prompt="test-prompt",
            is_empty=False,
        )
        log_b = PlatformWorkLog.create(
            user_id=user_b.id,
            target_date=date(2025, 8, 1),
            platform=PlatformEnum.GITHUB,
            content="B 작업",
            model_name="test-model",
            prompt="test-prompt",
            is_empty=False,
        )
        db_session.add_all([log_a, log_b])
        db_session.flush()

        chunk_a = PlatformWorkLogChunk.create(
            platform_work_log_id=log_a.id, chunk_index=0, chunk_text="A 청크"
        )
        chunk_a.update_embedding(embedding)
        chunk_b = PlatformWorkLogChunk.create(
            platform_work_log_id=log_b.id, chunk_index=0, chunk_text="B 청크"
        )
        chunk_b.update_embedding(embedding)
        db_session.add_all([chunk_a, chunk_b])
        db_session.flush()

        repository = PlatformWorkLogChunkRepository(db_session)

        # when
        results = repository.find_similar_by_embedding(
            user_id=user_a.id,
            query_embedding=embedding,
            similarity=0.5,
            limit=10,
        )

        # then — user_a의 청크만 반환
        assert len(results) == 1
        assert results[0].platform_work_log_chunk.chunk_text == "A 청크"

    def test_delete_by_platform_work_log_ids(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        work_log = platform_work_log_fixture(user_id=user.id)
        chunk = PlatformWorkLogChunk.create(
            platform_work_log_id=work_log.id,
            chunk_index=0,
            chunk_text="삭제 대상 청크",
        )
        db_session.add(chunk)
        db_session.flush()

        repository = PlatformWorkLogChunkRepository(db_session)

        # when
        repository.delete_by_platform_work_log_ids([work_log.id])

        # then
        remaining = repository.find_all_with_null_embedding()
        assert all(r.platform_work_log_id != work_log.id for r in remaining)
