from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser


class SlackSecretControllerTest:

    def test_슬랙_시크릿_목록_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        slack_secret_fixture,
    ):
        # given
        name = "My Slack Workspace"
        secret = slack_secret_fixture(name=name)

        # when
        response = auth_client.get("/api/v1/slack-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == secret.id
        assert data[0]["name"] == name

    def test_슬랙_시크릿_여러건_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        slack_secret_fixture,
    ):
        # given
        for i in range(3):
            slack_secret_fixture(name=f"Workspace {i}", bot_token=f"xoxb-token-{i}")

        # when
        response = auth_client.get("/api/v1/slack-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_슬랙_시크릿_없을때_빈_리스트_반환(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.get("/api/v1/slack-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_슬랙_시크릿_응답에_bot_token_미포함(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        slack_secret_fixture,
    ):
        # given
        slack_secret_fixture()

        # when
        response = auth_client.get("/api/v1/slack-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert "bot_token" not in data[0]
