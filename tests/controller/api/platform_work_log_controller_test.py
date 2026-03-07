from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser
from dev_blackbox.core.enum import PlatformEnum


class PlatformWorkLogControllerTest:

    def test_플랫폼_업무일지_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        platform_work_log_fixture,
    ):
        # given
        target_date = date(2025, 1, 1)
        work_log = platform_work_log_fixture(
            user_id=authenticated_user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            content="GitHub 활동 요약",
        )

        # when
        response = auth_client.get(
            "/api/v1/platform-work-logs",
            params={"target_date": str(target_date)},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == work_log.id
        assert data[0]["platform"] == PlatformEnum.GITHUB.value
        assert data[0]["content"] == "GitHub 활동 요약"
        assert data[0]["target_date"] == str(target_date)

    def test_플랫폼_업무일지_없을때_빈_리스트_반환(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # given
        target_date = date(2025, 1, 1)

        # when
        response = auth_client.get(
            "/api/v1/platform-work-logs",
            params={"target_date": str(target_date)},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_여러_플랫폼_업무일지_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        platform_work_log_fixture,
    ):
        # given
        target_date = date(2025, 1, 1)
        platform_work_log_fixture(
            user_id=authenticated_user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
        )
        platform_work_log_fixture(
            user_id=authenticated_user.id,
            target_date=target_date,
            platform=PlatformEnum.JIRA,
        )

        # when
        response = auth_client.get(
            "/api/v1/platform-work-logs",
            params={"target_date": str(target_date)},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_깃허브_업무일지에_이벤트_소스_포함(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        platform_work_log_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        target_date = date(2025, 1, 1)
        platform_work_log_fixture(
            user_id=authenticated_user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
        )
        secret = github_user_secret_fixture(user_id=authenticated_user.id)
        github_event_fixture(
            user_id=authenticated_user.id,
            github_user_secret_id=secret.id,
            target_date=target_date,
        )

        # when
        response = auth_client.get(
            "/api/v1/platform-work-logs",
            params={"target_date": str(target_date)},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert len(data[0]["github_events"]) == 1
        assert data[0]["jira_events"] == []
        assert data[0]["slack_messages"] == []

    def test_target_date_누락시_400(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.get("/api/v1/platform-work-logs")

        # then
        assert response.status_code == 400

    @patch(
        "dev_blackbox.controller.api.platform_work_log_controller"
        ".collect_events_and_summarize_work_log_by_user_task"
    )
    def test_수동_동기화_요청(
        self,
        mock_task,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # given
        request_body = {"target_date": "2025-01-01"}

        # when
        response = auth_client.post(
            "/api/v1/platform-work-logs/sync",
            json=request_body,
            headers={"Idempotency-Key": "test-key-001"},
        )

        # then
        assert response.status_code == 202
        data = response.json()
        assert "수동 동기화" in data["message"]

    @patch(
        "dev_blackbox.controller.api.platform_work_log_controller"
        ".collect_events_and_summarize_work_log_by_user_task"
    )
    def test_동일_멱등성키로_중복_요청시_409(
        self,
        mock_task,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # given
        request_body = {"target_date": "2025-01-01"}
        idempotency_key = "duplicate-key-001"
        headers = {"Idempotency-Key": idempotency_key}

        auth_client.post(
            "/api/v1/platform-work-logs/sync",
            json=request_body,
            headers=headers,
        )

        # when
        response = auth_client.post(
            "/api/v1/platform-work-logs/sync",
            json=request_body,
            headers=headers,
        )

        # then
        assert response.status_code == 422
