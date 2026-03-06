from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.daily_work_log_service import DailyWorkLogService
from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.user import User


class DailyWorkLogServiceTest:

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
        service = DailyWorkLogService(db_session)

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
        service = DailyWorkLogService(db_session)

        # when
        result = service.get_daily_work_log(user.id, date(2025, 1, 1))

        # then
        assert result is None

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
        service = DailyWorkLogService(db_session)

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
        service = DailyWorkLogService(db_session)

        # when
        result = service.save_daily_work_log(user.id, date(2025, 1, 1))

        # then
        assert result.content == ""
