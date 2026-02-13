from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from dev_blackbox.core.exception import EntityNotFoundException, ServiceException


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(EntityNotFoundException)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, exc: ServiceException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": exc.message},
        )
