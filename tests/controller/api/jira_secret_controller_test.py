from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser


class JiraSecretControllerTest:

    def test_지라_시크릿_목록_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
    ):
        # given
        name = "My Jira"
        url = "https://my-jira.atlassian.net"
        secret = jira_secret_fixture(name=name, url=url)

        # when
        response = auth_client.get("/api/v1/jira-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == secret.id
        assert data[0]["name"] == name
        assert data[0]["url"] == url

    def test_지라_시크릿_여러건_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
    ):
        # given
        for i in range(3):
            jira_secret_fixture(
                name=f"Jira {i}",
                url=f"https://jira-{i}.atlassian.net",
                username=f"user_{i}",
                api_token=f"token_{i}",
            )

        # when
        response = auth_client.get("/api/v1/jira-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_지라_시크릿_없을때_빈_리스트_반환(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.get("/api/v1/jira-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_지라_시크릿_응답에_민감정보_미포함(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
    ):
        # given
        jira_secret_fixture()

        # when
        response = auth_client.get("/api/v1/jira-secrets")

        # then
        assert response.status_code == 200
        data = response.json()
        assert "username" not in data[0]
        assert "api_token" not in data[0]
