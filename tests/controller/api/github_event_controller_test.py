from datetime import date

from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser


class GitHubEventControllerTest:

    def test_깃허브_이벤트_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        secret = github_user_secret_fixture(user_id=authenticated_user.id)
        target_date = date(2025, 1, 1)
        event = github_event_fixture(
            user_id=authenticated_user.id,
            github_user_secret_id=secret.id,
            target_date=target_date,
        )

        # when
        response = auth_client.get("/api/v1/github-events")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == event.id
        assert data[0]["event_id"] == event.event_id
        assert data[0]["event_type"] == "PushEvent"
        assert data[0]["target_date"] == str(target_date)

    def test_깃허브_이벤트_없을때_빈_리스트_반환(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.get("/api/v1/github-events")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_다른_사용자의_이벤트는_조회되지_않음(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        other_user = user_fixture(email="other@dev.com")
        secret = github_user_secret_fixture(user_id=other_user.id, username="other_user")
        github_event_fixture(
            user_id=other_user.id,
            github_user_secret_id=secret.id,
        )

        # when
        response = auth_client.get("/api/v1/github-events")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data == []
