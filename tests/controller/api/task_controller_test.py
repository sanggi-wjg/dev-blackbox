from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser
from dev_blackbox.core.enum import TaskStatusEnum


class TaskControllerTest:

    def test_태스크_목록_조회(
        self, auth_client: TestClient, authenticated_user: AuthenticatedUser, task_fixture
    ):
        # given
        task_fixture(user_id=authenticated_user.id, title="태스크 1", status=TaskStatusEnum.TODO)
        task_fixture(
            user_id=authenticated_user.id, title="태스크 2", status=TaskStatusEnum.IN_PROGRESS
        )

        # when
        response = auth_client.get("/api/v1/tasks")

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_태스크_상태_필터_조회(
        self, auth_client: TestClient, authenticated_user: AuthenticatedUser, task_fixture
    ):
        # given
        task_fixture(user_id=authenticated_user.id, title="할 일", status=TaskStatusEnum.TODO)
        task_fixture(
            user_id=authenticated_user.id, title="진행 중", status=TaskStatusEnum.IN_PROGRESS
        )

        # when
        response = auth_client.get(
            "/api/v1/tasks",
            params={"status": TaskStatusEnum.TODO.value},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "할 일"

    def test_태스크_생성(self, auth_client: TestClient, authenticated_user: AuthenticatedUser):
        # given
        request_body = {
            "title": "새 태스크",
            "status": TaskStatusEnum.TODO.value,
            "content": "태스크 내용",
            "tags": "python,fastapi",
            "display_order": 1,
        }

        # when
        response = auth_client.post("/api/v1/tasks", json=request_body)

        # then
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "새 태스크"
        assert data["content"] == "태스크 내용"
        assert data["tags"] == "python,fastapi"
        assert data["status"] == TaskStatusEnum.TODO.value
        assert data["display_order"] == 1
        assert data["is_archived"] is False

    def test_태스크_수정(
        self, auth_client: TestClient, authenticated_user: AuthenticatedUser, task_fixture
    ):
        # given
        task = task_fixture(
            user_id=authenticated_user.id, title="원래 제목", status=TaskStatusEnum.TODO
        )
        request_body = {
            "title": "수정된 제목",
            "content": "수정된 내용",
            "tags": None,
            "status": TaskStatusEnum.IN_PROGRESS.value,
            "display_order": 2,
        }

        # when
        response = auth_client.put(f"/api/v1/tasks/{task.id}", json=request_body)

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "수정된 제목"
        assert data["content"] == "수정된 내용"
        assert data["status"] == TaskStatusEnum.IN_PROGRESS.value
        assert data["display_order"] == 2

    def test_존재하지_않는_태스크_수정시_404(self, auth_client: TestClient):
        # given
        request_body = {
            "title": "수정",
            "status": TaskStatusEnum.TODO.value,
        }

        # when
        response = auth_client.put("/api/v1/tasks/999999", json=request_body)

        # then
        assert response.status_code == 404

    def test_태스크_삭제(
        self, auth_client: TestClient, authenticated_user: AuthenticatedUser, task_fixture
    ):
        # given
        task = task_fixture(user_id=authenticated_user.id)

        # when
        response = auth_client.delete(f"/api/v1/tasks/{task.id}")

        # then
        assert response.status_code == 204

    def test_태스크_아카이브(
        self, auth_client: TestClient, authenticated_user: AuthenticatedUser, task_fixture
    ):
        # given
        task = task_fixture(user_id=authenticated_user.id)

        # when
        response = auth_client.patch(f"/api/v1/tasks/{task.id}/archive")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is True
        assert data["archived_at"] is not None

    def test_태스크_아카이브_해제(
        self, auth_client: TestClient, authenticated_user: AuthenticatedUser, task_fixture
    ):
        # given
        task = task_fixture(user_id=authenticated_user.id)
        auth_client.patch(f"/api/v1/tasks/{task.id}/archive")

        # when
        response = auth_client.patch(f"/api/v1/tasks/{task.id}/unarchive")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["is_archived"] is False

    def test_태스크_순서_변경(
        self, auth_client: TestClient, authenticated_user: AuthenticatedUser, task_fixture
    ):
        # given
        task1 = task_fixture(user_id=authenticated_user.id, title="첫 번째", display_order=0)
        task2 = task_fixture(user_id=authenticated_user.id, title="두 번째", display_order=1)
        task3 = task_fixture(user_id=authenticated_user.id, title="세 번째", display_order=2)

        # when
        response = auth_client.patch(
            "/api/v1/tasks/reorder",
            json={"task_ids": [task3.id, task2.id, task1.id]},
        )

        # then
        assert response.status_code == 200
        data = response.json()
        assert data[0]["title"] == "세 번째"
        assert data[0]["display_order"] == 0
        assert data[1]["title"] == "두 번째"
        assert data[1]["display_order"] == 1
        assert data[2]["title"] == "첫 번째"
        assert data[2]["display_order"] == 2
