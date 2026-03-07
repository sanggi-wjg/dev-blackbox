from typing import Callable

from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser
from dev_blackbox.storage.rds.entity.user import User


class AdminUserControllerTest:

    def test_전체_사용자_목록_조회(
        self,
        admin_client: TestClient,
        authenticated_admin_user: AuthenticatedUser,
        user_fixture: Callable[..., User],
    ):
        # given
        user_fixture(email="user1@dev.com")
        user_fixture(email="user2@dev.com")

        # when
        response = admin_client.get("/admin-api/v1/users")

        # then
        assert response.status_code == 200
        data = response.json()
        emails = {u["email"] for u in data}
        assert "user1@dev.com" in emails
        assert "user2@dev.com" in emails
        assert authenticated_admin_user.email in emails

    def test_사용자가_없으면_관리자만_반환(
        self,
        admin_client: TestClient,
        authenticated_admin_user: AuthenticatedUser,
    ):
        # when
        response = admin_client.get("/admin-api/v1/users")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == authenticated_admin_user.email

    def test_사용자_생성(
        self,
        admin_client: TestClient,
    ):
        # given
        request_body = {
            "name": "새 사용자",
            "email": "new@dev.com",
            "password": "password123",
            "timezone": "Asia/Seoul",
        }

        # when
        response = admin_client.post("/admin-api/v1/users", json=request_body)

        # then
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == request_body["name"]
        assert data["email"] == request_body["email"]
        assert data["timezone"] == request_body["timezone"]
        assert "id" in data

    def test_사용자_생성시_기본_타임존은_서울(
        self,
        admin_client: TestClient,
    ):
        # given
        request_body = {
            "name": "새 사용자",
            "email": "default-tz@dev.com",
            "password": "password123",
        }

        # when
        response = admin_client.post("/admin-api/v1/users", json=request_body)

        # then
        assert response.status_code == 201
        data = response.json()
        assert data["timezone"] == "Asia/Seoul"

    def test_사용자_생성시_잘못된_타임존이면_400(
        self,
        admin_client: TestClient,
    ):
        # given
        request_body = {
            "name": "새 사용자",
            "email": "bad-tz@dev.com",
            "password": "password123",
            "timezone": "Invalid/Timezone",
        }

        # when
        response = admin_client.post("/admin-api/v1/users", json=request_body)

        # then
        assert response.status_code == 400

    def test_사용자_생성시_이름이_빈_문자열이면_400(
        self,
        admin_client: TestClient,
    ):
        # given
        request_body = {
            "name": "   ",
            "email": "blank@dev.com",
            "password": "password123",
        }

        # when
        response = admin_client.post("/admin-api/v1/users", json=request_body)

        # then
        assert response.status_code == 400

    def test_사용자_삭제(
        self,
        admin_client: TestClient,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture(email="to-delete@dev.com")

        # when
        response = admin_client.delete(f"/admin-api/v1/users/{user.id}")

        # then
        assert response.status_code == 204

    def test_존재하지_않는_사용자_삭제시_404(
        self,
        admin_client: TestClient,
    ):
        # when
        response = admin_client.delete("/admin-api/v1/users/999999")

        # then
        assert response.status_code == 404
