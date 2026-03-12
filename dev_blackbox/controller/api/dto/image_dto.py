from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from dev_blackbox.storage.rds.entity.image import Image


class ImageResponseDto(BaseModel):
    id: int
    filename: str
    content_type: str
    file_size: int

    @classmethod
    def from_entity(cls, entity: Image) -> ImageResponseDto:
        return cls(
            id=entity.id,
            filename=entity.filename,
            content_type=entity.content_type,
            file_size=entity.file_size,
        )
