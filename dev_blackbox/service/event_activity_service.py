from datetime import timedelta, date

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.domain.calculator import calculate_contribution_level
from dev_blackbox.service.model.event_activity_model import (
    EventContributionByDate,
    EventContribution,
    EventContributionSummary,
)
from dev_blackbox.service.query.event_activity_query import EventContributionQuery
from dev_blackbox.storage.rds.repository import (
    GitHubEventRepository,
    JiraEventRepository,
    SlackMessageRepository,
)


class EventActivityService:

    def __init__(self, session: Session):
        self.github_event_repository = GitHubEventRepository(session)
        self.jira_event_repository = JiraEventRepository(session)
        self.slack_message_repository = SlackMessageRepository(session)

    # @cacheable(CacheKey.EVENT_ACTIVITY, CacheTTL.HOURS_1)
    def get_event_contribution(self, query: EventContributionQuery) -> EventContribution:
        github = self._get_github_event_count_by_date(query)
        jira = self._get_jira_event_count_by_date(query)
        slack = self._get_slack_message_count_by_date(query)
        event_contribution = self._create_event_contribution(
            query=query,
            github=github,
            jira=jira,
            slack=slack,
        )
        return event_contribution

    def _create_event_contribution(
        self,
        query: EventContributionQuery,
        github: dict[date, int],
        jira: dict[date, int],
        slack: dict[date, int],
    ) -> EventContribution:
        contributions: list[EventContributionByDate] = []

        current_streak = 0
        longest_streak = 0
        active_days = 0

        diff_days = query.to_date - query.from_date
        max_count = 0

        for i in range(diff_days.days + 1):
            event_date = query.from_date + timedelta(days=i)
            github_count = github.get(event_date, 0)
            jira_count = jira.get(event_date, 0)
            slack_count = slack.get(event_date, 0)
            subtotal_count = github_count + jira_count + slack_count
            max_count = max(max_count, subtotal_count)

            if subtotal_count > 0:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
                active_days += 1
            else:
                current_streak = 0

            contributions.append(
                EventContributionByDate(
                    event_date=event_date,
                    count=subtotal_count,
                    level=0,
                    platforms={
                        PlatformEnum.GITHUB: github_count,
                        PlatformEnum.JIRA: jira_count,
                        PlatformEnum.SLACK: slack_count,
                    },
                )
            )

        for c in contributions:
            c.level = calculate_contribution_level(c.count, max_count)

        return EventContribution(
            summary=EventContributionSummary(
                total_contributions=sum(c.count for c in contributions),
                active_days=active_days,
                longest_streak=longest_streak,
                current_streak=current_streak,
            ),
            contributions=contributions,
        )

    def _get_github_event_count_by_date(self, query: EventContributionQuery) -> dict[date, int]:
        counts = self.github_event_repository.count_by_user_id_and_dates_group_by_date(
            user_id=query.user_id,
            from_date=query.from_date,
            to_date=query.to_date,
        )
        return {c.target_date: c.event_count for c in counts}

    def _get_jira_event_count_by_date(self, query: EventContributionQuery) -> dict[date, int]:
        counts = self.jira_event_repository.count_by_user_id_and_dates_group_by_date(
            user_id=query.user_id,
            from_date=query.from_date,
            to_date=query.to_date,
        )
        return {c.target_date: c.event_count for c in counts}

    def _get_slack_message_count_by_date(self, query: EventContributionQuery) -> dict[date, int]:
        counts = self.slack_message_repository.count_by_user_id_and_dates_group_by_date(
            user_id=query.user_id,
            from_date=query.from_date,
            to_date=query.to_date,
        )
        return {c.target_date: c.event_count for c in counts}
