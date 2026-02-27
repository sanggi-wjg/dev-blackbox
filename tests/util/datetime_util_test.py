from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from dev_blackbox.util.datetime_util import (
    get_daily_timestamp_range,
    get_date_from_iso_format,
    get_datetime_utc_now,
    get_yesterday,
    is_timestamp_in_range,
)


def test_get_datetime_utc_now():
    # given
    before = datetime.now(UTC)

    # when
    result = get_datetime_utc_now()

    # then
    after = datetime.now(UTC)
    assert result.tzinfo is not None
    assert before <= result <= after


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

    assert oldest == start_dt.timestamp()
    assert latest == end_dt.timestamp()


def test_is_timestamp_in_range():
    # given
    tz_info = ZoneInfo("Asia/Seoul")
    target_date = date(2026, 2, 15)
    target_datetime = datetime(2026, 2, 15, 12, tzinfo=tz_info)

    oldest, latest = get_daily_timestamp_range(target_date, tz_info)

    # when
    result = is_timestamp_in_range(target_datetime.timestamp(), oldest, latest)

    # then
    assert result
