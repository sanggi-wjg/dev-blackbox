from typing import Callable
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret


class AdminSlackSecretControllerTest:

    def test_Slack_시크릿_생성(
        self,
        admin_client: TestClient,
    ):
        # given
        request_body = {
            "name": "Test Slack",
            "bot_token": "xoxb-test-token",
        }

        # when
        response = admin_client.post("/admin-api/v1/slack-secrets", json=request_body)

        # then
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == request_body["name"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_Slack_시크릿_목록_조회(
        self,
        admin_client: TestClient,
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        slack_secret_fixture(name="Slack A")
        slack_secret_fixture(name="Slack B")

        # when
        response = admin_client.get("/admin-api/v1/slack-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        names = {s["name"] for s in data}
        assert "Slack A" in names
        assert "Slack B" in names

    def test_Slack_시크릿이_없으면_빈_리스트_반환(
        self,
        admin_client: TestClient,
    ):
        # when
        response = admin_client.get("/admin-api/v1/slack-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_Slack_시크릿_삭제(
        self,
        admin_client: TestClient,
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        secret = slack_secret_fixture()

        # when
        response = admin_client.delete(f"/admin-api/v1/slack-secrets/{secret.id}")

        # then
        assert response.status_code == 204

    def test_존재하지_않는_Slack_시크릿_삭제시_404(
        self,
        admin_client: TestClient,
    ):
        # when
        response = admin_client.delete("/admin-api/v1/slack-secrets/999999")

        # then
        assert response.status_code == 404

    @patch("dev_blackbox.service.slack_secret_service.get_slack_client")
    def test_Slack_사용자_동기화(
        self,
        mock_get_slack_client: MagicMock,
        admin_client: TestClient,
        slack_secret_fixture: Callable[..., SlackSecret],
    ):
        # given
        secret = slack_secret_fixture()
        mock_slack_client = MagicMock()
        mock_slack_client.fetch_users.return_value = []
        mock_get_slack_client.return_value = mock_slack_client

        # when
        response = admin_client.post(f"/admin-api/v1/slack-secrets/{secret.id}/sync")

        # then
        assert response.status_code == 200

    def test_존재하지_않는_Slack_시크릿_동기화시_404(
        self,
        admin_client: TestClient,
    ):
        # when
        response = admin_client.post("/admin-api/v1/slack-secrets/999999/sync")

        # then
        assert response.status_code == 404
