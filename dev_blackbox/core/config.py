import os
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel
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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
