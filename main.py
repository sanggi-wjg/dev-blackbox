from dev_blackbox.core.logging import setup_logging

setup_logging()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from dev_blackbox.controller.exception_handler import register_exception_handlers
from dev_blackbox.controller.api.github_event_controller import router as github_event_router
from dev_blackbox.controller.api.github_user_secret_controller import router as github_secret_router
from dev_blackbox.controller.health_controller import router as health_router
from dev_blackbox.controller.home_controller import router as home_router
from dev_blackbox.controller.api.jira_secret_controller import router as jira_secret_router
from dev_blackbox.controller.api.jira_user_controller import router as jira_user_router
from dev_blackbox.controller.api.slack_user_controller import router as slack_user_router
from dev_blackbox.controller.api.work_log_controller import router as work_log_router
from dev_blackbox.controller.api.user_controller import router as user_router
from dev_blackbox.controller.api.auth_controller import router as auth_router
from dev_blackbox.controller.admin.admin_jira_secret_controller import (
    router as admin_jira_secret_router,
)
from dev_blackbox.controller.admin.admin_user_controller import router as admin_user_router
from dev_blackbox.core.config import get_settings
from dev_blackbox.core.database import engine
from dev_blackbox.core.middleware import RequestIdMiddleware
from dev_blackbox.core.background_scheduler import scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown(wait=True)
    engine.dispose()


settings = get_settings()

app = FastAPI(
    lifespan=lifespan,
    title="Dev Blackbox API",
    version="0.1.1",
    openapi_version="3.0.3",
    docs_url=None if settings.is_prod else "/docs",
    redoc_url=None if settings.is_prod else "/redoc",
    openapi_url=None if settings.is_prod else "/openapi.json",
)
app.add_middleware(GZipMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)
register_exception_handlers(app)

# Api
app.include_router(home_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(github_secret_router)
app.include_router(github_event_router)
app.include_router(jira_secret_router)
app.include_router(jira_user_router)
app.include_router(slack_user_router)
app.include_router(work_log_router)

# Admin
app.include_router(admin_user_router)
app.include_router(admin_jira_secret_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=True,
        use_colors=True,
        log_config=None,  # setup_logging()에서 설정한 중앙 로깅 사용
    )
