from fastapi import APIRouter, status

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, str],
)
def health_check():
    # todo add health check (db, cache, etc...)
    # add  liveness probe, readiness probe
    return {"status": "healthy"}
