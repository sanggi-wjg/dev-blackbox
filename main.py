from fastapi import FastAPI, BackgroundTasks
from starlette import status

from dev_blackbox.controller.exception_handler import register_exception_handlers
from dev_blackbox.controller.github_user_secret_controller import router as github_secret_router
from dev_blackbox.controller.user_controller import router as user_router
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.task.collect_task import collect_by_platform_task

app = FastAPI()
register_exception_handlers(app)
app.include_router(user_router)
app.include_router(github_secret_router)


@app.get("/", status_code=status.HTTP_200_OK, tags=["Root"])
async def root():
    return {"message": "Hello World"}


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy"}


@app.post(
    "/collect/{platform}",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Collect"],
)
async def collect_platform_data(
    platform: PlatformEnum,
    user_id: int,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(collect_by_platform_task, platform=platform, user_id=user_id)
    return {"message": "Collection task started for platform."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=3,
        reload=True,
        reload_delay=5.0,
        access_log=True,
        use_colors=True,
    )
