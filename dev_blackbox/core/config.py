import os
from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, field_validator
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
    isolation_level: Literal["REPEATABLE READ"] = "REPEATABLE READ"

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class EncryptionSecrets(BaseModel):
    key: str
    pepper: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(_PROJECT_ROOT, ".env"),
        env_file_encoding="UTF-8",
        env_nested_delimiter="__",
        nested_model_default_partial_update=False,
    )

    database: PostgresDatabaseSecrets
    encryption: EncryptionSecrets

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
