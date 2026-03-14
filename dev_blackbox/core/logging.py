import logging.config
import os

from dev_blackbox.core.config import get_settings


def setup_logging() -> None:
    """
    main.py 최상단에서 다른 모듈 import 전에 호출해야 한다.
    """
    config = get_settings().logging
    handlers = config.handlers
    os.makedirs(config.log_file_dir, exist_ok=True)

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
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filename": os.path.join(config.log_file_dir, "app.log"),
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": config.level,
                "handlers": handlers,
            },
            "loggers": {
                "uvicorn": {
                    "level": config.uvicorn_level,
                    "handlers": handlers,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": config.uvicorn_level,
                    "handlers": handlers,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": config.uvicorn_level,
                    "handlers": handlers,
                    "propagate": False,
                },
                "apscheduler": {
                    "level": config.apscheduler_level,
                    "handlers": handlers,
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": config.sqlalchemy_level,
                    "handlers": handlers,
                    "propagate": False,
                },
            },
        }
    )
