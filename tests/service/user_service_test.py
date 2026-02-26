import pytest

from dev_blackbox.controller.admin.dto.user_dto import CreateUserRequestDto
from dev_blackbox.core.exception import UserNotFoundException
from dev_blackbox.service.user_service import UserService
from dev_blackbox.storage.rds.condition import UserSearchCondition


class UserServiceTest:

    def test_create_user(self, db_session):
        # given
        service = UserService(db_session)
        request = CreateUserRequestDto(
            name="테스트유저",
            email="test@dev.com",
            password="password123",
        )

        # when
        user = service.create_user(request)

        # then
        assert user.id is not None
        assert user.name == request.name
        assert user.email == request.email
        assert user.password != request.password

    def test_create_admin_user(self, db_session):
        # given
        service = UserService(db_session)
        request = CreateUserRequestDto(
            name="관리자",
            email="admin@dev.com",
            password="password123",
        )

        # when
        user = service.create_admin_user(request)

        # then
        assert user.id is not None
        assert user.name == request.name
        assert user.email == request.email
        assert user.password != request.password
        assert user.is_admin is True

    def test_get_user_by_id_or_throw(self, db_session, user_fixture):
        # given
        service = UserService(db_session)
        user = user_fixture("find@dev.com")

        # when
        result = service.get_user_by_id_or_throw(user.id)

        # then
        assert result == user

    def test_get_user_by_id_or_throw_존재하지_않으면_예외(self, db_session):
        # given
        service = UserService(db_session)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.get_user_by_id_or_throw(9999)

    def test_get_user_by_email_or_none(self, db_session, user_fixture):
        # given
        service = UserService(db_session)
        user = user_fixture("email@dev.com")

        # when
        result = service.get_user_by_email_or_none("email@dev.com")

        # then
        assert result == user

    def test_get_user_by_email_or_none_존재하지_않으면_None(self, db_session):
        # given
        service = UserService(db_session)

        # when
        result = service.get_user_by_email_or_none("nonexist@dev.com")

        # then
        assert result is None

    def test_authenticate(self, db_session, user_fixture):
        # given
        service = UserService(db_session)
        user_fixture("auth@dev.com", password="correct-password")

        # when
        result = service.authenticate("auth@dev.com", "correct-password")

        # then
        assert result is not None
        assert result.email == "auth@dev.com"

    def test_authenticate_이메일이_없으면_None(self, db_session):
        # given
        service = UserService(db_session)

        # when
        result = service.authenticate("nonexist@dev.com", "correct-password")

        # then
        assert result is None

    def test_authenticate_비밀번호가_틀리면_None(self, db_session, user_fixture):
        # given
        service = UserService(db_session)
        user_fixture("wrong-pw@dev.com", password="correct-password")

        # when
        result = service.authenticate("wrong-pw@dev.com", "wrong-password")

        # then
        assert result is None

    def test_create_jwt_token(self, db_session, user_fixture):
        # given
        service = UserService(db_session)
        user = user_fixture("jwt@dev.com")

        # when
        token = service.create_jwt_token(user)

        # then
        decoded = service.jwt_service.decode_token(token)
        assert decoded["sub"] == "jwt@dev.com"
        assert decoded["is_admin"] == user.is_admin

    def test_get_users(self, db_session, user_fixture):
        # given
        service = UserService(db_session)
        user1 = user_fixture("user1@dev.com")
        user2 = user_fixture("user2@dev.com")

        # when
        result = service.get_users()

        # then
        assert result == [user1, user2]

    def test_get_users_by_condition(self, db_session, user_fixture):
        # given
        service = UserService(db_session)
        user_fixture("alice@dev.com")
        bob = user_fixture("bob@dev.com")
        bob.name = "bob"
        db_session.flush()

        # when
        result = service.get_users_by_condition(UserSearchCondition(name="bob"))

        # then
        assert result == [bob]

    def test_delete_user(self, db_session, user_fixture):
        # given
        service = UserService(db_session)
        user = user_fixture("delete@dev.com")

        # when
        service.delete_user(user.id)

        # then
        assert user.is_deleted is True
        assert user.deleted_at is not None

    def test_delete_user_존재하지_않으면_예외(self, db_session):
        # given
        service = UserService(db_session)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.delete_user(9999)
