from dev_blackbox.storage.rds.repository import ImageRepository


class ImageRepositoryTest:

    def test_save(self, db_session, user_fixture, image_fixture):
        repository = ImageRepository(db_session)

        # given
        user = user_fixture("img_save@dev.com")
        image = image_fixture(user_id=user.id)

        # when
        result = repository.find_by_id_and_user_id(image.id, user.id)

        # then
        assert result is not None
        assert result.id == image.id
        assert result.filename == "test.png"
        assert result.content_type == "image/png"
        assert result.data == b"fake-image-data"

    def test_find_by_id_and_user_id(self, db_session, user_fixture, image_fixture):
        repository = ImageRepository(db_session)

        # given
        user = user_fixture("img_find@dev.com")
        image = image_fixture(user_id=user.id)

        # when
        result = repository.find_by_id_and_user_id(image.id, user.id)

        # then
        assert result is not None
        assert result.id == image.id

    def test_find_by_id_and_user_id_다른_유저(self, db_session, user_fixture, image_fixture):
        repository = ImageRepository(db_session)

        # given
        owner = user_fixture("img_owner@dev.com")
        other = user_fixture("img_other@dev.com")
        image = image_fixture(user_id=owner.id)

        # when
        result = repository.find_by_id_and_user_id(image.id, other.id)

        # then
        assert result is None

    def test_find_all_by_user_id(self, db_session, user_fixture, image_fixture):
        repository = ImageRepository(db_session)

        # given
        user = user_fixture("img_list@dev.com")
        other = user_fixture("img_list_other@dev.com")
        image1 = image_fixture(user_id=user.id, filename="a.png")
        image2 = image_fixture(user_id=user.id, filename="b.png")
        image_fixture(user_id=other.id, filename="c.png")

        # when
        result = repository.find_all_by_user_id(user.id)

        # then
        assert len(result) == 2
        result_ids = {r.id for r in result}
        assert image1.id in result_ids
        assert image2.id in result_ids

    def test_delete_by_id_and_user_id(self, db_session, user_fixture, image_fixture):
        repository = ImageRepository(db_session)

        # given
        user = user_fixture("img_delete@dev.com")
        image = image_fixture(user_id=user.id)

        # when
        repository.delete_by_id_and_user_id(image.id, user.id)

        # then
        result = repository.find_by_id_and_user_id(image.id, user.id)
        assert result is None
