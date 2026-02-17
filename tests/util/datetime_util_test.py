from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from dev_blackbox.util.datetime_util import (
    get_daily_timestamp_range,
    get_date_from_iso_format,
    get_yesterday,
)


def test_get_date_from_iso_format():
    # given
    iso_datetime = "2026-02-14T15:30:00Z"
    tz_info = ZoneInfo("Asia/Seoul")

    # when
    result = get_date_from_iso_format(iso_datetime, tz_info)

    # then
    assert result == date(2026, 2, 15)


def test_get_yesterday():
    # given
    tz_info = ZoneInfo("Asia/Seoul")

    # when
    result = get_yesterday(tz_info)

    # then
    expected = datetime.now(tz_info).date() - timedelta(days=1)
    assert result == expected


def test_get_daily_timestamp_range():
    # given
    target_date = date(2026, 2, 15)
    tz_info = ZoneInfo("Asia/Seoul")

    # when
    oldest, latest = get_daily_timestamp_range(target_date, tz_info)

    # then
    start_dt = datetime(2026, 2, 15, tzinfo=tz_info)
    end_dt = datetime(2026, 2, 16, tzinfo=tz_info)
    assert oldest == str(start_dt.timestamp())
    assert latest == str(end_dt.timestamp())
