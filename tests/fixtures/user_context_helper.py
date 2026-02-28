from zoneinfo import ZoneInfo

from dev_blackbox.task.context.user_context import UserContext


def create_user_context(
    id: int = 1,
    tz_info: ZoneInfo = ZoneInfo("Asia/Seoul"),
    has_github_user_secret: bool = False,
    has_jira_user: bool = False,
    has_slack_user: bool = False,
) -> UserContext:
    return UserContext(
        id=id,
        tz_info=tz_info,
        has_github_user_secret=has_github_user_secret,
        has_jira_user=has_jira_user,
        has_slack_user=has_slack_user,
    )
