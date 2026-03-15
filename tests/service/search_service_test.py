from datetime import date
from typing import Callable
from unittest.mock import patch, MagicMock

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.query.search_query import SearchQuery
from dev_blackbox.service.search_service import SearchService
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.user import User


class SearchServiceTest:

    @patch("dev_blackbox.service.search_service.get_embedding_agent")
    def test_search_platform_work_logs(
        self,
        mock_get_agent: MagicMock,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        embedding = [1.0] + [0.0] * 1023
        log = PlatformWorkLog.create(
            user_id=user.id,
            target_date=date(2025, 7, 1),
            platform=PlatformEnum.GITHUB,
            content="인증 모듈 리팩터링",
            model_name="test-model",
            prompt="test-prompt",
            is_empty=False,
        )
        log.update_embedding(embedding)
        db_session.add(log)
        db_session.flush()

        mock_agent = MagicMock()
        mock_agent.get_embedding.return_value = embedding
        mock_get_agent.return_value = mock_agent

        service = SearchService(db_session)
        query = SearchQuery(user_id=user.id, query_text="인증 관련 작업", limit=10)

        # when
        results = service.search_platform_work_logs(query)

        # then
        assert len(results) == 1
        assert results[0].platform_work_log.content == "인증 모듈 리팩터링"
        mock_agent.get_embedding.assert_called_once_with("인증 관련 작업")

    @patch("dev_blackbox.service.search_service.get_embedding_agent")
    def test_search_platform_work_logs_결과_없음(
        self,
        mock_get_agent: MagicMock,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        mock_agent = MagicMock()
        mock_agent.get_embedding.return_value = [1.0] + [0.0] * 1023
        mock_get_agent.return_value = mock_agent

        service = SearchService(db_session)
        query = SearchQuery(user_id=user.id, query_text="검색어", limit=10)

        # when
        results = service.search_platform_work_logs(query)

        # then
        assert len(results) == 0
