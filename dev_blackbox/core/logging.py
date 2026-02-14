import logging.config

from dev_blackbox.core.config import get_settings


def setup_logging() -> None:
    """중앙 집중식 로깅 설정. main.py 최상단에서 다른 모듈 import 전에 호출한다."""
    config = get_settings().logging

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": config.format,
                    "datefmt": config.date_format,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": config.level,
                "handlers": ["console"],
            },
            "loggers": {
                "uvicorn": {
                    "level": config.uvicorn_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": config.uvicorn_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": config.uvicorn_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
                "apscheduler": {
                    "level": config.apscheduler_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": config.sqlalchemy_level,
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )
