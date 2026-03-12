from sqlalchemy import delete, select
from sqlalchemy.orm import Session, load_only

from dev_blackbox.storage.rds.entity.image import Image


class ImageRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, image: Image) -> Image:
        self.session.add(image)
        self.session.flush()
        return image

    def find_by_id_and_user_id(self, image_id: int, user_id: int) -> Image | None:
        stmt = select(Image).where(
            Image.id == image_id,
            Image.user_id == user_id,
        )
        return self.session.scalar(stmt)

    def find_all_by_user_id(self, user_id: int) -> list[Image]:
        stmt = (
            select(Image)
            .options(
                load_only(
                    Image.id,
                    Image.user_id,
                    Image.filename,
                    Image.content_type,
                    Image.file_size,
                    Image.created_at,
                    Image.updated_at,
                )
            )
            .where(Image.user_id == user_id)
            .order_by(Image.created_at.desc())
        )
        return list(self.session.scalars(stmt))

    def delete_by_id_and_user_id(self, image_id: int, user_id: int) -> None:
        stmt = delete(Image).where(
            Image.id == image_id,
            Image.user_id == user_id,
        )
        self.session.execute(stmt)
        self.session.flush()
