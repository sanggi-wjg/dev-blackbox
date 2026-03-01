from fastapi import APIRouter, status

router = APIRouter(tags=["Home"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, str],
)
async def index():
    return {"message": "Hello World"}
