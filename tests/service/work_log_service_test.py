from datetime import date
from typing import Callable

import pytest
from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.core.exception import UserContentNotFoundException
from dev_blackbox.service.work_log_service import WorkLogService
from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.user import User


class WorkLogServiceTest:

    # ── get_platform_work_logs ──

    def test_get_platform_work_logs(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        work_log = platform_work_log_fixture(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
        )
        service = WorkLogService(db_session)

        # when
        result = service.get_platform_work_logs(user.id, target_date, [PlatformEnum.GITHUB])

        # then
        assert result == [work_log]

    def test_get_platform_work_logs_다른_플랫폼은_조회되지_않음(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        platform_work_log_fixture(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
        )
        service = WorkLogService(db_session)

        # when
        result = service.get_platform_work_logs(user.id, target_date, [PlatformEnum.JIRA])

        # then
        assert result == []

    def test_get_platform_work_logs_비어있으면_빈_리스트(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = WorkLogService(db_session)

        # when
        result = service.get_platform_work_logs(user.id, date(2025, 1, 1), PlatformEnum.all())

        # then
        assert result == []

    # ── save_platform_work_log ──

    def test_save_platform_work_log(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        service = WorkLogService(db_session)

        # when
        result = service.save_platform_work_log(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            content="GitHub summary",
            model_name="llama3",
            prompt="Summarize commits",
        )

        # then
        assert result.user_id == user.id
        assert result.platform == PlatformEnum.GITHUB
        assert result.content == "GitHub summary"

    def test_save_platform_work_log_기존_데이터_삭제_후_재저장(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        platform_work_log_fixture(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            content="Old content",
        )
        service = WorkLogService(db_session)

        # when
        result = service.save_platform_work_log(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            content="New content",
            model_name="llama3",
            prompt="Summarize commits",
        )

        # then
        assert result.content == "New content"
        all_logs = service.get_platform_work_logs(user.id, target_date, [PlatformEnum.GITHUB])
        assert len(all_logs) == 1

    # ── get_daily_work_log ──

    def test_get_daily_work_log(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        daily_work_log_fixture: Callable[..., DailyWorkLog],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        work_log = daily_work_log_fixture(user_id=user.id, target_date=target_date)
        service = WorkLogService(db_session)

        # when
        result = service.get_daily_work_log(user.id, target_date)

        # then
        assert result == work_log

    def test_get_daily_work_log_없으면_None(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = WorkLogService(db_session)

        # when
        result = service.get_daily_work_log(user.id, date(2025, 1, 1))

        # then
        assert result is None

    # ── get_daily_work_logs ──

    def test_get_daily_work_logs(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        daily_work_log_fixture: Callable[..., DailyWorkLog],
    ):
        # given
        user = user_fixture()
        log1 = daily_work_log_fixture(
            user_id=user.id, target_date=date(2025, 1, 1), content="Day 1"
        )
        log2 = daily_work_log_fixture(
            user_id=user.id, target_date=date(2025, 1, 2), content="Day 2"
        )
        service = WorkLogService(db_session)

        # when
        result = service.get_daily_work_logs(user.id)

        # then
        # target_date DESC 정렬
        assert result == [log2, log1]

    def test_get_daily_work_logs_비어있으면_빈_리스트(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = WorkLogService(db_session)

        # when
        result = service.get_daily_work_logs(user.id)

        # then
        assert result == []

    # ── save_daily_work_log ──

    def test_save_daily_work_log(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        platform_work_log_fixture(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            content="GitHub summary",
        )
        platform_work_log_fixture(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.JIRA,
            content="Jira summary",
        )
        service = WorkLogService(db_session)

        # when
        result = service.save_daily_work_log(user.id, target_date)

        # then
        assert "# GITHUB" in result.content
        assert "GitHub summary" in result.content
        assert "# JIRA" in result.content
        assert "Jira summary" in result.content

    def test_save_daily_work_log_플랫폼_워크로그가_없으면_빈_내용(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = WorkLogService(db_session)

        # when
        result = service.save_daily_work_log(user.id, date(2025, 1, 1))

        # then
        assert result.content == ""

    def test_save_daily_work_log_USER_CONTENT는_제외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        platform_work_log_fixture(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            content="GitHub summary",
        )
        platform_work_log_fixture(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.USER_CONTENT,
            content="User input",
        )
        service = WorkLogService(db_session)

        # when
        result = service.save_daily_work_log(user.id, target_date)

        # then
        assert "User input" not in result.content
        assert "GitHub summary" in result.content

    # ── get_user_content_or_none ──

    def test_get_user_content_or_none(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        work_log = platform_work_log_fixture(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.USER_CONTENT,
            content="User note",
            model_name="",
            prompt="",
        )
        service = WorkLogService(db_session)

        # when
        result = service.get_user_content_or_none(user.id, target_date)

        # then
        # @cacheable 데코레이터가 직렬화/역직렬화하므로 객체 참조가 달라질 수 있음
        assert result is not None
        assert result.id == work_log.id
        assert result.content == "User note"

    def test_get_user_content_or_none_없으면_None(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = WorkLogService(db_session)

        # when
        result = service.get_user_content_or_none(user.id, date(2025, 1, 1))

        # then
        assert result is None

    # ── create_or_update_user_content ──

    def test_create_or_update_user_content_생성(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        service = WorkLogService(db_session)

        # when
        is_created, result = service.create_or_update_user_content(
            user.id, target_date, "My note"
        )

        # then
        assert is_created is True
        assert result.content == "My note"
        assert result.platform == PlatformEnum.USER_CONTENT

    def test_create_or_update_user_content_수정(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        platform_work_log_fixture: Callable[..., PlatformWorkLog],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        platform_work_log_fixture(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.USER_CONTENT,
            content="Old note",
            model_name="",
            prompt="",
        )
        service = WorkLogService(db_session)

        # when
        is_created, result = service.create_or_update_user_content(
            user.id, target_date, "Updated note"
        )

        # then
        assert is_created is False
        assert result.content == "Updated note"

    # ── update_user_content ──

    def test_update_user_content_존재하지_않으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = WorkLogService(db_session)

        # when & then
        with pytest.raises(UserContentNotFoundException):
            service.update_user_content(user.id, date(2025, 1, 1), "content")
