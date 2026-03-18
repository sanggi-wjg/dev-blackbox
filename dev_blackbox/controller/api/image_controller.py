from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from dev_blackbox.controller.api.dto.image_dto import ImageResponseDto
from dev_blackbox.controller.config.security_config import AuthToken, CurrentUser
from dev_blackbox.core.database import get_db
from dev_blackbox.service.command.image_command import SaveImageCommand
from dev_blackbox.service.image_service import ImageService

router = APIRouter(prefix="/api/v1/images", tags=["Image"])


@router.post(
    "",
    response_model=ImageResponseDto,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    file: UploadFile,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed.",
        )

    data = await file.read()
    command = SaveImageCommand(
        user_id=current_user.id,
        filename=file.filename or "unknown",
        content_type=file.content_type,
        file_size=len(data),
        data=data,
    )
    service = ImageService(db)
    image = service.save_image(command)
    return ImageResponseDto.from_entity(image)


@router.get(
    "",
    response_model=list[ImageResponseDto],
    status_code=status.HTTP_200_OK,
)
def get_images(
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = ImageService(db)
    images = service.get_images(current_user.id)
    return [ImageResponseDto.from_entity(image) for image in images]


@router.get(
    "/{image_id}",
    status_code=status.HTTP_200_OK,
)
def get_image(
    image_id: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = ImageService(db)
    image = service.get_image_or_throw(image_id, current_user.id)
    return StreamingResponse(
        BytesIO(image.data),
        media_type=image.content_type,
    )


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_image(
    image_id: int,
    token: AuthToken,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    service = ImageService(db)
    service.delete_image(image_id, current_user.id)
    return None
