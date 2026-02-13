import os
from functools import lru_cache
from typing import Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PostgresDatabaseSecrets(BaseModel):
    debug: bool = True
    host: str
    port: str
    database: str
    user: str
    password: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 60
    pool_recycle: int = 1800
    pool_pre_ping: bool = True
    isolation_level: str = "REPEATABLE READ"

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class GithubSecrets(BaseModel):
    enabled: bool = False
    personal_access_token: str | None = None
    username: str | None = None

    @model_validator(mode='after')
    def validate_model(self) -> Self:
        if not self.enabled:
            self.personal_access_token = None
            self.username = None
            return self

        if not self.personal_access_token:
            raise ValueError(
                "⚙️ When GITHUB__ENABLED=True, `GITHUB__PERSONAL_ACCESS_TOKEN` must be set."
            )
        if not self.username:
            raise ValueError("⚙️ When GITHUB__ENABLED=True, `GITHUB__USERNAME` must be set.")
        return self


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(_PROJECT_ROOT, ".env"),
        env_file_encoding="UTF-8",
        env_nested_delimiter="__",
        nested_model_default_partial_update=False,
    )

    timezone: str = "Asia/Seoul"
    database: PostgresDatabaseSecrets
    github: GithubSecrets = Field(default_factory=GithubSecrets)

    @property
    def tz_info(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, KeyError) as _:
            raise ValueError(
                f"🌍 '{v}' is not a valid timezone. (e.g., UTC, Asia/Seoul, US/Eastern)"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
