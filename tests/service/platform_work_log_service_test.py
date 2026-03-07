from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from dev_blackbox.core.enum import PlatformEnum
from dev_blackbox.service.command.platform_work_log_command import SavePlatformWorkLogCommand
from dev_blackbox.service.platform_work_log_service import PlatformWorkLogService
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.user import User


class PlatformWorkLogServiceTest:

    # ── save_platform_work_log ──

    def test_save_platform_work_log(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        target_date = date(2025, 1, 1)
        service = PlatformWorkLogService(db_session)

        # when
        command = SavePlatformWorkLogCommand(
            user_id=user.id,
            target_date=target_date,
            platform=PlatformEnum.GITHUB,
            content="GitHub summary",
            model_name="llama3",
            prompt="Summarize commits",
        )
        result = service.save_platform_work_log(command)

        # then
        assert result.user_id == user.id
        assert result.platform == PlatformEnum.GITHUB
        assert result.content == "GitHub summary"
