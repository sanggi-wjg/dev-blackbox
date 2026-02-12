from datetime import date, datetime
from zoneinfo import ZoneInfo


def get_date_from_iso_format(iso_datetime: str, tz_info: ZoneInfo) -> date:
    return datetime.fromisoformat(iso_datetime).astimezone(tz_info).date()
