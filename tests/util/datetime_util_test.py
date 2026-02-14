from datetime import date
from zoneinfo import ZoneInfo

from dev_blackbox.util.datetime_util import get_date_from_iso_format


def test_get_date_from_iso_format():
    # given
    iso_datetime = "2026-02-14T15:30:00Z"
    tz_info = ZoneInfo("Asia/Seoul")

    # when
    result = get_date_from_iso_format(iso_datetime, tz_info)

    # then
    assert result == date(2026, 2, 15)
