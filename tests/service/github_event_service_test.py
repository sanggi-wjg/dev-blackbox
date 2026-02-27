from datetime import date

from dev_blackbox.service.github_event_service import GitHubEventService


class GitHubEventServiceTest:

    def test_get_events_by_user_id(
        self,
        db_session,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)
        event = github_event_fixture(user_id=user.id, github_user_secret_id=secret.id)

        service = GitHubEventService(db_session)

        # when
        result = service.get_events_by_user_id(user.id)

        # then
        assert result == [event]

    def test_get_events_by_user_id_이벤트가_없으면_빈_리스트(self, db_session, user_fixture):
        # given
        user = user_fixture()
        service = GitHubEventService(db_session)

        # when
        result = service.get_events_by_user_id(user.id)

        # then
        assert result == []

    def test_get_github_events(
        self,
        db_session,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        target_date = date(2025, 1, 1)
        another_date = date(2025, 1, 2)

        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)
        event = github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=target_date,
            event_id="event-id",
        )
        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=another_date,
            event_id="another-event-id",
        )

        service = GitHubEventService(db_session)

        # when
        result = service.get_github_events(user.id, target_date)

        # then
        assert result == [event]

    def test_get_github_events_이벤트가_없으면_빈_리스트(self, db_session, user_fixture):
        # given
        user = user_fixture()
        service = GitHubEventService(db_session)

        # when
        result = service.get_github_events(
            user.id,
            date(2025, 1, 1),
        )

        # then
        assert result == []
