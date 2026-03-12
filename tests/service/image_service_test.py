import pytest

from dev_blackbox.core.exception import ImageNotFoundException
from dev_blackbox.service.command.image_command import SaveImageCommand
from dev_blackbox.service.image_service import ImageService


class ImageServiceTest:

    def test_save_image(self, db_session, user_fixture):
        service = ImageService(db_session)

        # given
        user = user_fixture("img_svc_save@dev.com")
        command = SaveImageCommand(
            user_id=user.id,
            filename="photo.jpg",
            content_type="image/jpeg",
            file_size=1024,
            data=b"jpeg-data",
        )

        # when
        result = service.save_image(command)

        # then
        assert result.id is not None
        assert result.filename == "photo.jpg"
        assert result.content_type == "image/jpeg"
        assert result.file_size == 1024
        assert result.data == b"jpeg-data"

    def test_get_images(self, db_session, user_fixture, image_fixture):
        service = ImageService(db_session)

        # given
        user = user_fixture("img_svc_list@dev.com")
        image_fixture(user_id=user.id, filename="a.png")
        image_fixture(user_id=user.id, filename="b.png")

        # when
        result = service.get_images(user.id)

        # then
        assert len(result) == 2

    def test_get_image_or_throw(self, db_session, user_fixture, image_fixture):
        service = ImageService(db_session)

        # given
        user = user_fixture("img_svc_get@dev.com")
        image = image_fixture(user_id=user.id)

        # when
        result = service.get_image_or_throw(image.id, user.id)

        # then
        assert result.id == image.id

    def test_get_image_or_throw_404(self, db_session, user_fixture):
        service = ImageService(db_session)

        # given
        user = user_fixture("img_svc_404@dev.com")

        # when & then
        with pytest.raises(ImageNotFoundException):
            service.get_image_or_throw(999999, user.id)

    def test_delete_image(self, db_session, user_fixture, image_fixture):
        service = ImageService(db_session)

        # given
        user = user_fixture("img_svc_del@dev.com")
        image = image_fixture(user_id=user.id)

        # when
        service.delete_image(image.id, user.id)

        # then
        with pytest.raises(ImageNotFoundException):
            service.get_image_or_throw(image.id, user.id)

    def test_delete_image_404(self, db_session, user_fixture):
        service = ImageService(db_session)

        # given
        user = user_fixture("img_svc_del404@dev.com")

        # when & then
        with pytest.raises(ImageNotFoundException):
            service.delete_image(999999, user.id)
