from datetime import date
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.platform_work_log_chunk import PlatformWorkLogChunk


class SearchControllerTest:

    @patch("dev_blackbox.service.search_service.get_embedding_agent")
    def test_검색(
        self,
        mock_get_agent: MagicMock,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        db_session,
    ):
        # given
        embedding = [1.0] + [0.0] * 1023
        log = PlatformWorkLog.create(
            user_id=authenticated_user.id,
            target_date=date(2025, 8, 1),
            platform=PlatformEnum.GITHUB,
            content="인증 모듈 리팩터링",
            model_name="test-model",
            prompt="test-prompt",
            is_empty=False,
        )
        db_session.add(log)
        db_session.flush()

        chunk = PlatformWorkLogChunk.create(
            platform_work_log_id=log.id,
            chunk_index=0,
            chunk_text="인증 모듈 리팩터링",
        )
        chunk.update_embedding(embedding)
        db_session.add(chunk)
        db_session.flush()

        mock_agent = MagicMock()
        mock_agent.get_embedding.return_value = embedding
        mock_get_agent.return_value = mock_agent

        # when
        response = auth_client.get(
            "/api/v1/search",
            params={"query": "인증 관련 작업", "limit": 10},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["content"] == "인증 모듈 리팩터링"
        assert data["results"][0]["platform"] == "GITHUB"
        assert "score" in data["results"][0]

    def test_query_누락시_400(
        self,
        auth_client: TestClient,
    ):
        # given / when
        response = auth_client.get("/api/v1/search")

        # then
        assert response.status_code == 400

    @patch("dev_blackbox.service.search_service.get_embedding_agent")
    def test_결과_없으면_빈_배열(
        self,
        mock_get_agent: MagicMock,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # given
        mock_agent = MagicMock()
        mock_agent.get_embedding.return_value = [1.0] + [0.0] * 1023
        mock_get_agent.return_value = mock_agent

        # when
        response = auth_client.get(
            "/api/v1/search",
            params={"query": "존재하지 않는 검색어"},
        )

        # then
        assert response.status_code == 200
        assert response.json()["results"] == []
