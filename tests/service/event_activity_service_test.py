from datetime import date

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.event_activity_service import EventActivityService
from dev_blackbox.service.query.event_activity_query import EventContributionQuery


class EventActivityServiceTest:

    def test_get_event_contribution(
        self,
        db_session,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
        jira_secret_fixture,
        jira_user_fixture,
        jira_event_fixture,
        slack_secret_fixture,
        slack_user_fixture,
        slack_message_fixture,
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)

        secret = github_user_secret_fixture(user_id=user.id)
        github_event_fixture(
            user_id=user.id, github_user_secret_id=secret.id, target_date=target_date
        )

        jira_secret = jira_secret_fixture()
        jira_user = jira_user_fixture(jira_secret_id=jira_secret.id, user_id=user.id)
        jira_event_fixture(user_id=user.id, jira_user_id=jira_user.id, target_date=target_date)

        slack_secret = slack_secret_fixture()
        slack_user = slack_user_fixture(slack_secret_id=slack_secret.id, user_id=user.id)
        slack_message_fixture(user_id=user.id, slack_user_id=slack_user.id, target_date=target_date)

        service = EventActivityService(db_session)
        query = EventContributionQuery(
            from_date=target_date,
            to_date=target_date,
            user_id=user.id,
        )

        # when
        result = service.get_event_contribution(query)

        # then
        assert result.summary.total_contributions == 3
        assert result.summary.active_days == 1
        assert result.summary.longest_streak == 1
        assert result.summary.current_streak == 1
        assert len(result.contributions) == 1

        contribution = result.contributions[0]
        assert contribution.event_date == target_date
        assert contribution.count == 3
        assert contribution.level == 4
        assert contribution.platforms[PlatformEnum.GITHUB] == 1
        assert contribution.platforms[PlatformEnum.JIRA] == 1
        assert contribution.platforms[PlatformEnum.SLACK] == 1

    def test_get_event_contribution_이벤트가_없으면_모두_0(
        self,
        db_session,
        user_fixture,
    ):
        # given
        user = user_fixture()
        from_date = date(2025, 1, 1)
        to_date = date(2025, 1, 3)

        service = EventActivityService(db_session)
        query = EventContributionQuery(
            from_date=from_date,
            to_date=to_date,
            user_id=user.id,
        )

        # when
        result = service.get_event_contribution(query)

        # then
        assert result.summary.total_contributions == 0
        assert result.summary.active_days == 0
        assert result.summary.longest_streak == 0
        assert result.summary.current_streak == 0
        assert len(result.contributions) == 3

        for c in result.contributions:
            assert c.count == 0
            assert c.level == 0

    def test_get_event_contribution_날짜_범위_필터링(
        self,
        db_session,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)

        in_range_date = date(2025, 1, 2)
        out_of_range_date = date(2025, 1, 5)

        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=in_range_date,
            event_id="in-range-event",
        )
        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=out_of_range_date,
            event_id="out-of-range-event",
        )

        service = EventActivityService(db_session)
        query = EventContributionQuery(
            from_date=date(2025, 1, 1),
            to_date=date(2025, 1, 3),
            user_id=user.id,
        )

        # when
        result = service.get_event_contribution(query)

        # then
        assert result.summary.total_contributions == 1
        assert len(result.contributions) == 3

        date_counts = {c.event_date: c.count for c in result.contributions}
        assert date_counts[in_range_date] == 1
        assert date_counts[date(2025, 1, 1)] == 0
        assert date_counts[date(2025, 1, 3)] == 0

    def test_get_event_contribution_streak_계산(
        self,
        db_session,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)

        # 1/1, 1/2 연속 → 1/3 빈 날 → 1/4 활동
        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=date(2025, 1, 1),
            event_id="streak-1",
        )
        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=date(2025, 1, 2),
            event_id="streak-2",
        )
        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=date(2025, 1, 4),
            event_id="streak-3",
        )

        service = EventActivityService(db_session)
        query = EventContributionQuery(
            from_date=date(2025, 1, 1),
            to_date=date(2025, 1, 4),
            user_id=user.id,
        )

        # when
        result = service.get_event_contribution(query)

        # then
        assert result.summary.longest_streak == 2
        assert result.summary.current_streak == 1
        assert result.summary.active_days == 3

    def test_get_event_contribution_level_계산(
        self,
        db_session,
        user_fixture,
        github_user_secret_fixture,
        github_event_fixture,
    ):
        # given
        user = user_fixture()
        secret = github_user_secret_fixture(user_id=user.id)

        # 1/1: 4개 이벤트 (max), 1/2: 1개 이벤트 (25% → level 1)
        for i in range(4):
            github_event_fixture(
                user_id=user.id,
                github_user_secret_id=secret.id,
                target_date=date(2025, 1, 1),
                event_id=f"level-max-{i}",
            )
        github_event_fixture(
            user_id=user.id,
            github_user_secret_id=secret.id,
            target_date=date(2025, 1, 2),
            event_id="level-low",
        )

        service = EventActivityService(db_session)
        query = EventContributionQuery(
            from_date=date(2025, 1, 1),
            to_date=date(2025, 1, 2),
            user_id=user.id,
        )

        # when
        result = service.get_event_contribution(query)

        # then
        date_levels = {c.event_date: c.level for c in result.contributions}
        assert date_levels[date(2025, 1, 1)] == 4  # 100% → level 4
        assert date_levels[date(2025, 1, 2)] == 1  # 25% → level 1
