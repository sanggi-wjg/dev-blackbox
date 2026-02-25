from sqlalchemy import Enum

IDEMPOTENCY_TTL_SECONDS = 300
IDEMPOTENCY_PROCESSING_VALUE = "PROCESSING"

EMPTY_ACTIVITY_MESSAGE = "이 플랫폼에 대해 수집된 활동 데이터가 없습니다."

DEFAULT_CACHE_TTL_SECONDS = 60
CACHE_TTL_SECONDS_30 = 30


class CacheKey(str, Enum):
    WORK_LOG_PLATFORM = "work-logs-platforms:users:{user_id}:target_date:{target_date}"
    WORK_LOG_USER_CONTENT = "work-logs-user-content:users:{user_id}:target_date:{target_date}"
