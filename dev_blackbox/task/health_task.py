import logging

logger = logging.getLogger(__name__)


def health_check_task():
    logger.info("😎 정상 동작 중!")
    return {"status": "healthy"}
