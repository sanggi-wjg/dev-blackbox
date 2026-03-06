from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser


class SlackUserControllerTest:

    def test_슬랙_사용자_목록_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        slack_secret_fixture,
        slack_user_fixture,
    ):
        # given
        secret = slack_secret_fixture()
        slack_user_fixture(
            slack_secret_id=secret.id,
            member_id="U_TEST_001",
            display_name="테스트 사용자",
            real_name="Test User",
            email="slack@dev.com",
        )

        # when
        response = auth_client.get(
            "/api/v1/slack-users",
            params={"slack_secret_id": secret.id},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["display_name"] == "테스트 사용자"
        assert data[0]["real_name"] == "Test User"
        assert data[0]["email"] == "slack@dev.com"
        assert data[0]["member_id"] == "U_TEST_001"

    def test_슬랙_사용자_목록_전체_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        slack_secret_fixture,
        slack_user_fixture,
    ):
        # given
        secret = slack_secret_fixture()
        for i in range(3):
            slack_user_fixture(
                slack_secret_id=secret.id,
                member_id=f"U_TEST_{i}",
                display_name=f"사용자{i}",
                real_name=f"User {i}",
            )

        # when
        response = auth_client.get("/api/v1/slack-users")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_슬랙_사용자_할당(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        slack_secret_fixture,
        slack_user_fixture,
    ):
        # given
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(slack_secret_id=secret.id)

        # when
        response = auth_client.patch(
            "/api/v1/slack-users",
            json={
                "slack_secret_id": secret.id,
                "slack_user_id": slack_user.id,
            },
        )

        # then
        assert response.status_code == 204

    def test_슬랙_사용자_할당_해제(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        slack_secret_fixture,
        slack_user_fixture,
    ):
        # given
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(
            slack_secret_id=secret.id,
            user_id=authenticated_user.id,
        )

        # when
        response = auth_client.delete(f"/api/v1/slack-users/{slack_user.id}")

        # then
        assert response.status_code == 204

    def test_존재하지_않는_슬랙_사용자_할당_해제시_404(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.delete("/api/v1/slack-users/999999")

        # then
        assert response.status_code == 404

    def test_시크릿_불일치_슬랙_사용자_할당시_에러(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        slack_secret_fixture,
        slack_user_fixture,
    ):
        # given
        secret1 = slack_secret_fixture(name="Secret 1", bot_token="xoxb-token-1")
        secret2 = slack_secret_fixture(name="Secret 2", bot_token="xoxb-token-2")
        slack_user = slack_user_fixture(slack_secret_id=secret1.id, member_id="U_MISMATCH")

        # when
        response = auth_client.patch(
            "/api/v1/slack-users",
            json={
                "slack_secret_id": secret2.id,
                "slack_user_id": slack_user.id,
            },
        )

        # then
        assert response.status_code == 400
