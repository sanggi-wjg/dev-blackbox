from io import BytesIO

from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser
from dev_blackbox.service.command.image_command import SaveImageCommand
from dev_blackbox.service.image_service import ImageService


class ImageControllerTest:

    def test_이미지_업로드(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        db_session,
    ):
        # given
        file_data = b"fake-png-bytes"
        files = {"file": ("test.png", BytesIO(file_data), "image/png")}

        # when
        response = auth_client.post("/api/v1/images", files=files)

        # then
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.png"
        assert data["content_type"] == "image/png"
        assert data["file_size"] == len(file_data)

    def test_비이미지_파일_업로드시_400(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # given
        files = {"file": ("doc.txt", BytesIO(b"text data"), "text/plain")}

        # when
        response = auth_client.post("/api/v1/images", files=files)

        # then
        assert response.status_code == 400

    def test_이미지_목록_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        db_session,
    ):
        # given
        service = ImageService(db_session)
        for name in ["a.png", "b.png"]:
            service.save_image(
                SaveImageCommand(
                    user_id=authenticated_user.id,
                    filename=name,
                    content_type="image/png",
                    file_size=4,
                    data=b"data",
                )
            )

        # when
        response = auth_client.get("/api/v1/images")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert "data" not in data[0]  # data 필드 미포함 확인

    def test_이미지_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        db_session,
    ):
        # given
        service = ImageService(db_session)
        command = SaveImageCommand(
            user_id=authenticated_user.id,
            filename="view.png",
            content_type="image/png",
            file_size=10,
            data=b"image-data",
        )
        image = service.save_image(command)

        # when
        response = auth_client.get(f"/api/v1/images/{image.id}")

        # then
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == b"image-data"

    def test_존재하지_않는_이미지_조회시_404(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.get("/api/v1/images/999999")

        # then
        assert response.status_code == 404

    def test_이미지_삭제(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        db_session,
    ):
        # given
        service = ImageService(db_session)
        command = SaveImageCommand(
            user_id=authenticated_user.id,
            filename="delete-me.png",
            content_type="image/png",
            file_size=5,
            data=b"12345",
        )
        image = service.save_image(command)

        # when
        response = auth_client.delete(f"/api/v1/images/{image.id}")

        # then
        assert response.status_code == 204

    def test_존재하지_않는_이미지_삭제시_404(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
    ):
        # when
        response = auth_client.delete("/api/v1/images/999999")

        # then
        assert response.status_code == 404
