import logging
from datetime import UTC, datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from dev_blackbox.core.exception import (
    CompletedRequestException,
    ConflictRequestException,
    EntityNotFoundException,
    JiraUserSecretMismatchException,
    SlackUserSecretMismatchException,
    ServiceException,
)

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

    @app.exception_handler(ConflictRequestException)
    async def conflict_request_handler(request: Request, e: ConflictRequestException):
        logger.warning(e)

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": f"{status.HTTP_409_CONFLICT} CONFLICT",
                "error": "Request In Progress",
                "message": e.message,
                "path": request.url.path,
                "requestedAt": datetime.now(UTC.utc).isoformat(),
            },
        )

    @app.exception_handler(CompletedRequestException)
    async def completed_request_handler(request: Request, e: CompletedRequestException):
        logger.warning(e)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": f"{status.HTTP_422_UNPROCESSABLE_ENTITY} UNPROCESSABLE_ENTITY",
                "error": "Request Already Completed",
                "message": e.message,
                "response": e.cached_response,
                "path": request.url.path,
                "requestedAt": datetime.now(UTC.utc).isoformat(),
            },
        )

    @app.exception_handler(JiraUserSecretMismatchException)
    async def jira_user_secret_mismatch_handler(
        request: Request, e: JiraUserSecretMismatchException
    ):
        logger.warning(e)

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": f"{status.HTTP_400_BAD_REQUEST} BAD_REQUEST",
                "error": "Jira User Secret Mismatch",
                "message": e.message,
                "path": request.url.path,
                "requestedAt": datetime.now(UTC.utc).isoformat(),
            },
        )

    @app.exception_handler(SlackUserSecretMismatchException)
    async def slack_user_secret_mismatch_handler(
        request: Request, e: SlackUserSecretMismatchException
    ):
        logger.warning(e)

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": f"{status.HTTP_400_BAD_REQUEST} BAD_REQUEST",
                "error": "Slack User Secret Mismatch",
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

    @app.exception_handler(RequestValidationError)
    async def entity_request_validation_error(request: Request, e: RequestValidationError):
        logger.warning(e)
        body = {
            "status": f"{status.HTTP_400_BAD_REQUEST} BAD_REQUEST",
            "error": "Request Validation Error",
            "message": "Request validation failed, please check the request parameters.",
            "details": e.errors(),
            "path": request.url.path,
            "requestedAt": datetime.now(UTC.utc).isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=body,
        )
