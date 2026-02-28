import logging

logger = logging.getLogger(__name__)


def health_check_task():
    logger.info("😎 I'm healthy!")
    return {"status": "healthy"}
