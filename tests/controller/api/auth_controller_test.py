from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser


class AuthControllerTest:

    def test_정상_로그인(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # given
        form_data = {
            "username": "test@dev.com",
            "password": "password",
        }

        # when
        response = auth_client.post("/api/v1/auth/token", data=form_data)

        # then
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_존재하지_않는_이메일로_로그인시_401(
        self,
        auth_client: TestClient,
    ):
        # given
        form_data = {
            "username": "nonexistent@dev.com",
            "password": "password",
        }

        # when
        response = auth_client.post("/api/v1/auth/token", data=form_data)

        # then
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid credentials"

    def test_잘못된_비밀번호로_로그인시_401(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # given
        form_data = {
            "username": "test@dev.com",
            "password": "wrong_password",
        }

        # when
        response = auth_client.post("/api/v1/auth/token", data=form_data)

        # then
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid credentials"
