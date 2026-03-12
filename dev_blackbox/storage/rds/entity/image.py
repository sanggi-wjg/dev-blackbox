from sqlalchemy import BigInteger, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from dev_blackbox.storage.rds.entity.base import Base


class Image(Base):
    __tablename__ = "image"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Image(id={self.id}, user_id={self.user_id}, filename={self.filename})>"

    @classmethod
    def create(
        cls,
        user_id: int,
        filename: str,
        content_type: str,
        file_size: int,
        data: bytes,
    ) -> "Image":
        return cls(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            data=data,
        )
