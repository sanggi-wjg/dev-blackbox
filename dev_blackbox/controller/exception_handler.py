import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from dev_blackbox.core.exception import EntityNotFoundException, ServiceException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, e: Exception):
        logger.exception(e)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred."},
        )

    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, e: ServiceException):
        logger.exception(e)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": e.message},
        )

    @app.exception_handler(EntityNotFoundException)
    async def entity_not_found_handler(request: Request, e: EntityNotFoundException):
        logger.warning(e)

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": e.message},
        )
