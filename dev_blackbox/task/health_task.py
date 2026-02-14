import logging

logger = logging.getLogger(__name__)


def health_check_task():
    logger.info("Health check task executed")
    return {"status": "healthy"}
