from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.command.embedding_command import UpdatePlatformWorkLogEmbeddingCommand
from dev_blackbox.service.embedding_service import EmbeddingService
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.user import User


class EmbeddingServiceTest:

    def test_update_embedding(
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
            UpdatePlatformWorkLogEmbeddingCommand(
                work_log_id=work_log.id,
                embedding=fake_embedding,
            )
        ]
        service = EmbeddingService(db_session)

        # when
        service.update_embedding(commands)

        # then
        db_session.flush()
        updated = db_session.get(PlatformWorkLog, work_log.id)
        assert updated is not None
        assert updated.embedding == fake_embedding

    def test_update_embedding_여러건(
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
            UpdatePlatformWorkLogEmbeddingCommand(work_log_id=work_log_1.id, embedding=embedding_1),
            UpdatePlatformWorkLogEmbeddingCommand(work_log_id=work_log_2.id, embedding=embedding_2),
        ]
        service = EmbeddingService(db_session)

        # when
        service.update_embedding(commands)

        # then
        db_session.flush()
        updated_1 = db_session.get(PlatformWorkLog, work_log_1.id)
        updated_2 = db_session.get(PlatformWorkLog, work_log_2.id)
        assert updated_1 is not None
        assert updated_1.embedding == embedding_1
        assert updated_2 is not None
        assert updated_2.embedding == embedding_2

    def test_update_embedding_빈_커맨드(
        self,
        db_session: Session,
    ):
        # given
        service = EmbeddingService(db_session)

        # when / then — 에러 없이 완료
        service.update_embedding([])
