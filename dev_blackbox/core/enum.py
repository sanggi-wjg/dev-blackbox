from enum import Enum


class PlatformEnum(str, Enum):
    GITHUB = "GITHUB"
    JIRA = "JIRA"
    CONFLUENCE = "CONFLUENCE"
    SLACK = "SLACK"
    USER_CONTENT = "USER_CONTENT"

    @classmethod
    def all(cls) -> list[PlatformEnum]:
        return [member for member in cls]

    @classmethod
    def platforms(cls) -> list[PlatformEnum]:
        return [member for member in cls if member != PlatformEnum.USER_CONTENT]


class DistributedLockName(str, Enum):
    SYNC_JIRA_USERS_TASK = "sync_jira_users_task"
    SYNC_SLACK_USERS_TASK = "sync_slack_users_task"
    COLLECT_EVENTS_AND_SUMMARIZE_WORK_LOG_TASK = "collect_events_and_summarize_work_log_task"
