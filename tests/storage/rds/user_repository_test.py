from dev_blackbox.storage.rds.repository import UserRepository


class UserRepositoryTest:

    def test_find_by_id(self, db_session, user_fixture):
        repository = UserRepository(db_session)

        # given
        user = user_fixture("iam@dev.com")

        # when
        result = repository.find_by_id(user.id)

        # then
        assert result == user

    def test_find_all(self, db_session, user_fixture):
        repository = UserRepository(db_session)

        # given
        user1 = user_fixture("user1@dev.com")
        user2 = user_fixture("user2@dev.com")

        # when
        result = repository.find_all()

        # then
        assert result == [user1, user2]
