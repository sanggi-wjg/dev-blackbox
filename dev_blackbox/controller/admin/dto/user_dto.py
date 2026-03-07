from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_core import PydanticCustomError

from dev_blackbox.core.types import NotBlankStr


class CreateUserRequestDto(BaseModel):
    name: NotBlankStr
    email: EmailStr
    password: NotBlankStr
    timezone: str = Field(default="Asia/Seoul")

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, KeyError) as _:
            raise PydanticCustomError(
                "invalid_timezone",
                "'{value}' is not a valid timezone. (e.g., UTC, Asia/Seoul, US/Eastern)",
                {"value": v},
            )
        return v
