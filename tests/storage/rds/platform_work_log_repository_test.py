from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.user import User
from dev_blackbox.storage.rds.repository import PlatformWorkLogRepository


class PlatformWorkLogRepositoryTest:

    def test_find_all_with_null_embedding(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 5, 1),
            platform=PlatformEnum.GITHUB,
            content="GitHub 요약",
        )
        platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 5, 1),
            platform=PlatformEnum.JIRA,
            content="",  # 빈 content
        )
        repository = PlatformWorkLogRepository(db_session)

        # when
        results = repository.find_all_with_null_embedding()

        # then — 빈 content는 제외
        assert len(results) == 1
        assert results[0].content == "GitHub 요약"

    def test_find_similar_by_embedding(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        embedding_a = [1.0] + [0.0] * 1023
        embedding_b = [0.0] + [1.0] + [0.0] * 1022

        log_a = PlatformWorkLog.create(
            user_id=user.id,
            target_date=date(2025, 2, 1),
            platform=PlatformEnum.GITHUB,
            content="인증 관련 작업",
            model_name="test-model",
            prompt="test-prompt",
            is_empty=False,
        )
        log_a.update_embedding(embedding_a)

        log_b = PlatformWorkLog.create(
            user_id=user.id,
            target_date=date(2025, 2, 2),
            platform=PlatformEnum.JIRA,
            content="배포 작업",
            model_name="test-model",
            prompt="test-prompt",
            is_empty=False,
        )
        log_b.update_embedding(embedding_b)

        db_session.add_all([log_a, log_b])
        db_session.flush()

        repository = PlatformWorkLogRepository(db_session)

        # when — embedding_a와 동일한 벡터로 검색
        results = repository.find_similar_by_embedding(
            user_id=user.id,
            query_embedding=embedding_a,
            limit=10,
        )

        # then — 가장 유사한 결과가 먼저 반환
        assert len(results) == 2
        assert results[0].platform_work_log.content == "인증 관련 작업"
        assert results[0].distance < results[1].distance

    def test_find_similar_by_embedding_임베딩_없는_레코드_제외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        platform_work_log_fixture(
            user_id=user.id,
            target_date=date(2025, 3, 1),
            platform=PlatformEnum.GITHUB,
        )  # embedding=None
        repository = PlatformWorkLogRepository(db_session)

        # when
        results = repository.find_similar_by_embedding(
            user_id=user.id,
            query_embedding=[1.0] + [0.0] * 1023,
            limit=10,
        )

        # then
        assert len(results) == 0

    def test_find_similar_by_embedding_다른_유저_제외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user_a = user_fixture("usera@dev.com")
        user_b = user_fixture("userb@dev.com")
        embedding = [1.0] + [0.0] * 1023

        log_a = PlatformWorkLog.create(
            user_id=user_a.id,
            target_date=date(2025, 4, 1),
            platform=PlatformEnum.GITHUB,
            content="A작업",
            model_name="test-model",
            prompt="test-prompt",
            is_empty=False,
        )
        log_a.update_embedding(embedding)

        log_b = PlatformWorkLog.create(
            user_id=user_b.id,
            target_date=date(2025, 4, 1),
            platform=PlatformEnum.GITHUB,
            content="B작업",
            model_name="test-model",
            prompt="test-prompt",
            is_empty=False,
        )
        log_b.update_embedding(embedding)

        db_session.add_all([log_a, log_b])
        db_session.flush()

        repository = PlatformWorkLogRepository(db_session)

        # when
        results = repository.find_similar_by_embedding(
            user_id=user_a.id,
            query_embedding=embedding,
            limit=10,
        )

        # then — user_a의 결과만 반환
        assert len(results) == 1
        assert results[0].platform_work_log.user_id == user_a.id
