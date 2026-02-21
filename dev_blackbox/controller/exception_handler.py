import logging
from datetime import UTC, datetime

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
            content={
                "status": f"{status.HTTP_500_INTERNAL_SERVER_ERROR} INTERNAL_SERVER_ERROR",
                "error": "Internal Server Error, please contact the administrator.",
                "path": request.url.path,
                "requestedAt": datetime.now(UTC.utc).isoformat(),
            },
        )

    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, e: ServiceException):
        logger.exception(e)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": f"{status.HTTP_500_INTERNAL_SERVER_ERROR} INTERNAL_SERVER_ERROR",
                "error": "Service Error, please contact the administrator.",
                "message": e.message,
                "path": request.url.path,
                "requestedAt": datetime.now(UTC.utc).isoformat(),
            },
        )

    @app.exception_handler(EntityNotFoundException)
    async def entity_not_found_handler(request: Request, e: EntityNotFoundException):
        logger.warning(e)

        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": f"{status.HTTP_404_NOT_FOUND} NOT_FOUND",
                "error": "Entity Not Found",
                "message": e.message,
                "path": request.url.path,
                "requestedAt": datetime.now(UTC.utc).isoformat(),
            },
        )
