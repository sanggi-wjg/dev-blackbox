from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser


class GitHubUserSecretControllerTest:

    def test_깃허브_시크릿_생성(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # given
        request_body = {
            "username": "my_github_user",
            "personal_access_token": "ghp_test_token_1234567890",
        }

        # when
        response = auth_client.post("/api/v1/github-secrets", json=request_body)

        # then
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == request_body["username"]
        assert "personal_access_token" in data
        assert data["personal_access_token"] != request_body["personal_access_token"]

    def test_이미_존재하는_시크릿_생성시_500(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        github_user_secret_fixture,
    ):
        # given
        github_user_secret_fixture(user_id=authenticated_user.id)
        request_body = {
            "username": "another_user",
            "personal_access_token": "ghp_another_token",
        }

        # when
        response = auth_client.post("/api/v1/github-secrets", json=request_body)

        # then
        assert response.status_code == 500

    def test_깃허브_시크릿_삭제(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        github_user_secret_fixture,
    ):
        # given
        github_user_secret_fixture(user_id=authenticated_user.id)

        # when
        response = auth_client.delete("/api/v1/github-secrets")

        # then
        assert response.status_code == 204

    def test_시크릿_없이_삭제시_404(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.delete("/api/v1/github-secrets")

        # then
        assert response.status_code == 404
