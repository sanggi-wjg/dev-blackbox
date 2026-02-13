from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from dev_blackbox.controller.exception_handler import register_exception_handlers
from dev_blackbox.controller.github_collect_controller import router as github_collect_router
from dev_blackbox.controller.github_event_controller import router as github_event_router
from dev_blackbox.controller.github_user_secret_controller import router as github_secret_router
from dev_blackbox.controller.health_controller import router as health_router
from dev_blackbox.controller.home_contoller import router as home_router
from dev_blackbox.controller.user_controller import router as user_router
from dev_blackbox.task.background_scheduler import scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title="Dev Blackbox API",
    version="0.1.0",
)
app.add_middleware(GZipMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
register_exception_handlers(app)

app.include_router(home_router)
app.include_router(health_router)
app.include_router(user_router)
app.include_router(github_secret_router)
app.include_router(github_collect_router)
app.include_router(github_event_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_delay=5.0,
        access_log=True,
        use_colors=True,
    )
