from fastapi import FastAPI, BackgroundTasks
from starlette import status

from dev_blackbox.controller.exception_handler import register_exception_handlers
from dev_blackbox.controller.user_controller import router as user_router
from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.task.collect_task import collect_by_platform_task

app = FastAPI()
register_exception_handlers(app)
app.include_router(user_router)


@app.get("/")
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
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(collect_by_platform_task, platform=platform)
    return {"message": "Collection task started for platform."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        use_colors=True,
    )
