from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def get_date_from_iso_format(iso_datetime: str, tz_info: ZoneInfo) -> date:
    return datetime.fromisoformat(iso_datetime).astimezone(tz_info).date()


def get_yesterday(tz_info: ZoneInfo) -> date:
    return datetime.now(tz_info).date() - timedelta(days=1)


def get_daily_timestamp_range(target_date: date, tz_info: ZoneInfo) -> tuple[float, float]:
    """
    target_date를 날짜 기준 시작/종료 Unix timestamp 문자열로 변환
    """
    start_dt = datetime(target_date.year, target_date.month, target_date.day, tzinfo=tz_info)
    end_dt = start_dt + timedelta(days=1)
    return start_dt.timestamp(), end_dt.timestamp()


def is_timestamp_in_range(
    timestamp: str | float,
    start_timestamp: float,
    end_timestamp: float,
) -> bool:
    if isinstance(timestamp, str):
        timestamp = float(timestamp)
    return float(start_timestamp) <= float(timestamp) < float(end_timestamp)
