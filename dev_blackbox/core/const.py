from enum import Enum

IDEMPOTENCY_TTL_SECONDS = 300
IDEMPOTENCY_PROCESSING_VALUE = "PROCESSING"

EMPTY_ACTIVITY_MESSAGE = "이 플랫폼에 대해 수집된 활동 데이터가 없습니다."


class CacheTTL(int, Enum):
    DEFAULT = 60
    SECONDS_30 = 30
    MINUTES_15 = 900


class CacheKey(str, Enum):
    WORK_LOG_PLATFORM = "work-logs-platforms:users:{user_id}:target_date:{target_date}"
    WORK_LOG_USER_CONTENT = "work-logs-user-content:users:{user_id}:target_date:{target_date}"


class LockKey(str, Enum):
    SYNC_JIRA_USERS_TASK = "sync_jira_users_task"
    SYNC_SLACK_USERS_TASK = "sync_slack_users_task"
    COLLECT_EVENTS_AND_SUMMARIZE_WORK_LOG_TASK = "collect_events_and_summarize_work_log_task"
