from datetime import date
from enum import StrEnum

from pydantic import BaseModel

from dev_blackbox.service.query.common_query import OrderDirection


class JiraEventOrderField(StrEnum):
    ID = "id"


class JiraEventQuery(BaseModel):
    user_id: int | None = None
    target_date: date | None = None
    order_by: list[tuple[JiraEventOrderField, OrderDirection]] = [
        (JiraEventOrderField.ID, OrderDirection.ASC)
    ]
