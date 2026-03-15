from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog
from dev_blackbox.storage.rds.entity.user import User
from dev_blackbox.storage.rds.repository import DailyWorkLogRepository


class DailyWorkLogRepositoryTest:

    def test_find_all_with_null_embedding(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        daily_work_log_fixture: Callable[..., DailyWorkLog],
    ):
        # given
        user = user_fixture()
        daily_work_log_fixture(user_id=user.id, target_date=date(2025, 1, 1), content="내용 있음")
        daily_work_log_fixture(user_id=user.id, target_date=date(2025, 1, 2), content="")
        repository = DailyWorkLogRepository(db_session)

        # when
        results = repository.find_all_with_null_embedding()

        # then — 빈 content("")는 제외
        assert len(results) == 1
        assert results[0].content == "내용 있음"
