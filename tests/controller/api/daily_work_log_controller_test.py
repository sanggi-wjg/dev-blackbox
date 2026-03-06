from datetime import date

from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser


class DailyWorkLogControllerTest:

    def test_일일_업무_일지_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        daily_work_log_fixture,
    ):
        # given
        target_date = date(2025, 1, 1)
        content = "Daily summary"
        daily_work_log_fixture(
            user_id=authenticated_user.id,
            target_date=target_date,
            content=content,
        )

        # when
        response = auth_client.get(
            "/api/v1/daily-work-logs",
            params={"target_date": target_date.isoformat()},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["target_date"] == target_date.isoformat()
        assert data["content"] == content
        assert data["user_id"] == authenticated_user.id

    def test_데이터가_없으면_null_반환(
        self,
        auth_client: TestClient,
    ):
        # given
        target_date = date(2025, 6, 1)

        # when
        response = auth_client.get(
            "/api/v1/daily-work-logs",
            params={"target_date": target_date.isoformat()},
        )

        # then
        assert response.status_code == 200
        assert response.json() is None

    def test_target_date_누락시_400(
        self,
        auth_client: TestClient,
    ):
        # given / when
        response = auth_client.get("/api/v1/daily-work-logs")

        # then
        assert response.status_code == 400
