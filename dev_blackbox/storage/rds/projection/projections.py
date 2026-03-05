from datetime import date
from typing import NamedTuple


class EventCountByDateProjection(NamedTuple):
    target_date: date
    event_count: int
