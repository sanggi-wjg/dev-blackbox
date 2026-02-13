from fastapi import FastAPI
from starlette import status

from dev_blackbox.controller.exception_handler import register_exception_handlers
from dev_blackbox.controller.github_collect_controller import router as github_collect_router
from dev_blackbox.controller.github_user_secret_controller import router as github_secret_router
from dev_blackbox.controller.user_controller import router as user_router

app = FastAPI()
register_exception_handlers(app)
app.include_router(user_router)
app.include_router(github_secret_router)
app.include_router(github_collect_router)


@app.get("/", status_code=status.HTTP_200_OK, tags=["Root"])
async def root():
    return {"message": "Hello World"}


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {"status": "healthy"}


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
