from typing import Callable
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from dev_blackbox.storage.rds.entity.jira_secret import JiraSecret


class AdminJiraSecretControllerTest:

    def test_Jira_시크릿_생성(
        self,
        admin_client: TestClient,
    ):
        # given
        request_body = {
            "name": "Test Jira",
            "url": "https://test.atlassian.net",
            "username": "jira_user",
            "api_token": "jira_token",
        }

        # when
        response = admin_client.post("/admin-api/v1/jira-secrets", json=request_body)

        # then
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == request_body["name"]
        assert data["url"] == request_body["url"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_Jira_시크릿_목록_조회(
        self,
        admin_client: TestClient,
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        jira_secret_fixture(name="Jira A", url="https://a.atlassian.net")
        jira_secret_fixture(name="Jira B", url="https://b.atlassian.net")

        # when
        response = admin_client.get("/admin-api/v1/jira-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        names = {s["name"] for s in data}
        assert "Jira A" in names
        assert "Jira B" in names

    def test_Jira_시크릿이_없으면_빈_리스트_반환(
        self,
        admin_client: TestClient,
    ):
        # when
        response = admin_client.get("/admin-api/v1/jira-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_Jira_시크릿_삭제(
        self,
        admin_client: TestClient,
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        secret = jira_secret_fixture()

        # when
        response = admin_client.delete(f"/admin-api/v1/jira-secrets/{secret.id}")

        # then
        assert response.status_code == 204

    def test_존재하지_않는_Jira_시크릿_삭제시_404(
        self,
        admin_client: TestClient,
    ):
        # when
        response = admin_client.delete("/admin-api/v1/jira-secrets/999999")

        # then
        assert response.status_code == 404

    @patch("dev_blackbox.service.jira_secret_service.get_jira_client")
    def test_Jira_사용자_동기화(
        self,
        mock_get_jira_client: MagicMock,
        admin_client: TestClient,
        jira_secret_fixture: Callable[..., JiraSecret],
    ):
        # given
        secret = jira_secret_fixture()
        request_body = {"project": "PROJ"}
        mock_jira_client = MagicMock()
        mock_jira_client.fetch_assignable_users.return_value = []
        mock_get_jira_client.return_value = mock_jira_client

        # when
        response = admin_client.post(
            f"/admin-api/v1/jira-secrets/{secret.id}/sync",
            json=request_body,
        )

        # then
        assert response.status_code == 200

    def test_존재하지_않는_Jira_시크릿_동기화시_404(
        self,
        admin_client: TestClient,
    ):
        # given
        request_body = {"project": "PROJ"}

        # when
        response = admin_client.post(
            "/admin-api/v1/jira-secrets/999999/sync",
            json=request_body,
        )

        # then
        assert response.status_code == 404
