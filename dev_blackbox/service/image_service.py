from sqlalchemy.orm import Session

from dev_blackbox.core.exception import ImageNotFoundException
from dev_blackbox.service.command.image_command import SaveImageCommand
from dev_blackbox.storage.rds.entity.image import Image
from dev_blackbox.storage.rds.repository import ImageRepository


class ImageService:

    def __init__(self, session: Session):
        self.image_repository = ImageRepository(session)

    def save_image(self, command: SaveImageCommand) -> Image:
        image = Image.create(
            user_id=command.user_id,
            filename=command.filename,
            content_type=command.content_type,
            file_size=command.file_size,
            data=command.data,
        )
        return self.image_repository.save(image)

    def get_images(self, user_id: int) -> list[Image]:
        return self.image_repository.find_all_by_user_id(user_id)

    def get_image_or_throw(self, image_id: int, user_id: int) -> Image:
        image = self.image_repository.find_by_id_and_user_id(image_id, user_id)
        if image is None:
            raise ImageNotFoundException(image_id)
        return image

    def delete_image(self, image_id: int, user_id: int) -> None:
        self.get_image_or_throw(image_id, user_id)
        self.image_repository.delete_by_id_and_user_id(image_id, user_id)
