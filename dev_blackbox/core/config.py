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


class RedisSecrets(BaseModel):
    host: str
    port: int


class EncryptionSecrets(BaseModel):
    key: str
    pepper: str


class AuthSecrets(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = 30


class SlackSecrets(BaseModel):
    bot_token: str


class LoggingConfig(BaseModel):
    level: str = "INFO"  # 루트 로거 레벨
    uvicorn_level: str = "INFO"
    apscheduler_level: str = "WARNING"
    sqlalchemy_level: str = "WARNING"
    format: str = (
        "%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)s | "
        "%(funcName)s:%(lineno)d — %(message)s"
    )
    date_format: str = "%Y-%m-%d %H:%M:%S"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(_PROJECT_ROOT, ".env"),
        env_file_encoding="UTF-8",
        env_nested_delimiter="__",
        nested_model_default_partial_update=False,
    )

    env: Literal["local", "dev", "stage", "prod"]
    database: PostgresDatabaseSecrets
    redis: RedisSecrets
    encryption: EncryptionSecrets
    auth: AuthSecrets
    slack: SlackSecrets
    logging: LoggingConfig = LoggingConfig()

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

    @property
    def cors_allow_origins(self) -> list[str]:
        if self.env == "local":
            return ["*"]
        return ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
