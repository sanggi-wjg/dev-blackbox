from datetime import date

from fastapi.testclient import TestClient

from dev_blackbox.controller.config.model.authenticated_user import AuthenticatedUser


class EventActivityControllerTest:

    def test_이벤트_활동_히트맵_조회(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        target_date = date(2025, 1, 1)
        secret = github_user_secret_fixture(user_id=authenticated_user.id)
        github_event_fixture(
            user_id=authenticated_user.id,
            github_user_secret_id=secret.id,
            target_date=target_date,
        )
        params = {
            "from_date": target_date.isoformat(),
            "to_date": target_date.isoformat(),
        }

        # when
        response = auth_client.get("/api/v1/event-activity/heatmap", params=params)

        # then
        assert response.status_code == 200
        data = response.json()

        summary = data["summary"]
        assert summary["total_contributions"] == 1
        assert summary["active_days"] == 1
        assert summary["longest_streak"] == 1
        assert summary["current_streak"] == 1

        contributions = data["contributions"]
        assert len(contributions) == 1
        assert contributions[0]["event_date"] == target_date.isoformat()
        assert contributions[0]["total_count"] == 1
        assert contributions[0]["level"] == 4
        assert contributions[0]["platforms"]["GITHUB"] == 1
        assert contributions[0]["platforms"]["JIRA"] == 0
        assert contributions[0]["platforms"]["SLACK"] == 0

    def test_활동_데이터가_없으면_빈_기여_반환(
        self,
        auth_client: TestClient,
    ):
        # given
        params = {
            "from_date": "2025-06-01",
            "to_date": "2025-06-03",
        }

        # when
        response = auth_client.get("/api/v1/event-activity/heatmap", params=params)

        # then
        assert response.status_code == 200
        data = response.json()

        summary = data["summary"]
        assert summary["total_contributions"] == 0
        assert summary["active_days"] == 0
        assert summary["longest_streak"] == 0
        assert summary["current_streak"] == 0

        contributions = data["contributions"]
        assert len(contributions) == 3
        for c in contributions:
            assert c["total_count"] == 0
            assert c["level"] == 0

    def test_필수_파라미터_누락시_400(
        self,
        auth_client: TestClient,
    ):
        # given / when
        response = auth_client.get("/api/v1/event-activity/heatmap")

        # then
        assert response.status_code == 400

    def test_여러_플랫폼_이벤트_집계(
        self,
        auth_client: TestClient,
        authenticated_user: AuthenticatedUser,
        github_user_secret_fixture,
        github_event_fixture,
        slack_secret_fixture,
        slack_user_fixture,
        slack_message_fixture,
    ):
        # given
        target_date = date(2025, 1, 1)
        secret = github_user_secret_fixture(user_id=authenticated_user.id)
        github_event_fixture(
            user_id=authenticated_user.id,
            github_user_secret_id=secret.id,
            target_date=target_date,
        )
        slack_secret = slack_secret_fixture()
        slack_user = slack_user_fixture(
            slack_secret_id=slack_secret.id,
            user_id=authenticated_user.id,
        )
        slack_message_fixture(
            user_id=authenticated_user.id,
            slack_user_id=slack_user.id,
            target_date=target_date,
        )
        params = {
            "from_date": target_date.isoformat(),
            "to_date": target_date.isoformat(),
        }

        # when
        response = auth_client.get("/api/v1/event-activity/heatmap", params=params)

        # then
        assert response.status_code == 200
        data = response.json()

        summary = data["summary"]
        assert summary["total_contributions"] == 2
        assert summary["active_days"] == 1

        contribution = data["contributions"][0]
        assert contribution["total_count"] == 2
        assert contribution["platforms"]["GITHUB"] == 1
        assert contribution["platforms"]["SLACK"] == 1
