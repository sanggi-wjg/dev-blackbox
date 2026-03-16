from enum import IntEnum, StrEnum

GITHUB_COMMIT_MAX_PATCH_LENGTH = 500

IDEMPOTENCY_PROCESSING_VALUE = "PROCESSING"

EMPTY_ACTIVITY_MESSAGE = "이 플랫폼에 대해 수집된 활동 데이터가 없습니다."


class CacheTTL(IntEnum):
    DEFAULT = 60
    SECONDS_30 = 30
    MINUTES_15 = 900
    HOURS_1 = 3600
    IDEMPOTENT_REQUEST = 300


class CacheKey(StrEnum):
    WORK_LOG_PLATFORM_QUERY = (
        "work-logs-platforms:users:{query.user_id}:target_date:{query.target_date}"
    )
    WORK_LOG_PLATFORM_COMMAND = (
        "work-logs-platforms:users:{command.user_id}:target_date:{command.target_date}"
    )
    EVENT_ACTIVITY = "event-activities:users:{query.user_id}:from:{query.from_date}:to:{query.to_date}:platforms:{query.platforms}:group_by:{query.group_by}"
    TEST_CACHE = "test:users:{user_id}:target_date:{target_date}"


class LockKey(StrEnum):
    SYNC_JIRA_USERS_TASK = "sync_jira_users_task"
    SYNC_JIRA_BACKLOG_TASK = "sync_jira_backlog_task"
    SYNC_SLACK_USERS_TASK = "sync_slack_users_task"
    COLLECT_EVENTS_AND_SUMMARIZE_WORK_LOG_TASK = "collect_events_and_summarize_work_log_task"
    GENERATE_PLATFORM_WORK_LOG_EMBEDDINGS_TASK = "generate_platform_work_log_embeddings_task"
