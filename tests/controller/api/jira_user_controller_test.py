from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser


class JiraUserControllerTest:

    def test_지라_사용자_목록_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
        jira_user_fixture,
    ):
        # given
        secret = jira_secret_fixture()
        account_id = "acc-001"
        display_name = "테스트 사용자"
        email_address = "jira@dev.com"
        jira_user_fixture(
            jira_secret_id=secret.id,
            account_id=account_id,
            display_name=display_name,
            email_address=email_address,
        )

        # when
        response = auth_client.get("/api/v1/jira-users")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["account_id"] == account_id
        assert data[0]["display_name"] == display_name
        assert data[0]["email_address"] == email_address
        assert data[0]["jira_secret_id"] == secret.id

    def test_지라_사용자_시크릿_ID로_필터링_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
        jira_user_fixture,
    ):
        # given
        secret1 = jira_secret_fixture(name="Jira 1", username="user1", api_token="token1")
        secret2 = jira_secret_fixture(name="Jira 2", username="user2", api_token="token2")
        jira_user_fixture(jira_secret_id=secret1.id, account_id="acc-s1")
        jira_user_fixture(jira_secret_id=secret2.id, account_id="acc-s2")

        # when
        response = auth_client.get(
            "/api/v1/jira-users",
            params={"jira_secret_id": secret1.id},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["jira_secret_id"] == secret1.id

    def test_지라_사용자_전체_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
        jira_user_fixture,
    ):
        # given
        secret = jira_secret_fixture()
        for i in range(3):
            jira_user_fixture(
                jira_secret_id=secret.id,
                account_id=f"acc-{i}",
                display_name=f"User {i}",
                email_address=f"user{i}@dev.com",
            )

        # when
        response = auth_client.get("/api/v1/jira-users")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_지라_사용자_없을때_빈_리스트_반환(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.get("/api/v1/jira-users")

        # then
        assert response.status_code == 200
        assert response.json() == []

    def test_지라_사용자_할당(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
        jira_user_fixture,
    ):
        # given
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(jira_secret_id=secret.id)
        request_body = {
            "jira_secret_id": secret.id,
            "jira_user_id": jira_user.id,
            "project": "DEV",
        }

        # when
        response = auth_client.patch("/api/v1/jira-users", json=request_body)

        # then
        assert response.status_code == 204

    def test_지라_사용자_할당_해제(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
        jira_user_fixture,
    ):
        # given
        secret = jira_secret_fixture()
        jira_user = jira_user_fixture(
            jira_secret_id=secret.id,
            user_id=authenticated_user.id,
            project="DEV",
        )

        # when
        response = auth_client.delete(f"/api/v1/jira-users/{jira_user.id}")

        # then
        assert response.status_code == 204

    def test_존재하지_않는_지라_사용자_할당_해제시_404(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.delete("/api/v1/jira-users/999999")

        # then
        assert response.status_code == 404

    def test_시크릿_불일치_지라_사용자_할당시_400(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
        jira_user_fixture,
    ):
        # given
        secret1 = jira_secret_fixture(name="Jira 1", username="user1", api_token="token1")
        secret2 = jira_secret_fixture(name="Jira 2", username="user2", api_token="token2")
        jira_user = jira_user_fixture(jira_secret_id=secret1.id, account_id="acc-mismatch")

        request_body = {
            "jira_secret_id": secret2.id,
            "jira_user_id": jira_user.id,
            "project": "DEV",
        }

        # when
        response = auth_client.patch("/api/v1/jira-users", json=request_body)

        # then
        assert response.status_code == 400

    def test_존재하지_않는_지라_사용자_할당시_404(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        jira_secret_fixture,
    ):
        # given
        secret = jira_secret_fixture()
        request_body = {
            "jira_secret_id": secret.id,
            "jira_user_id": 999999,
            "project": "DEV",
        }

        # when
        response = auth_client.patch("/api/v1/jira-users", json=request_body)

        # then
        assert response.status_code == 404
