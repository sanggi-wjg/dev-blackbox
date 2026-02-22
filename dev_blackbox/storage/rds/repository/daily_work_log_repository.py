from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.daily_work_log import DailyWorkLog


class DailyWorkLogRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, daily_work_log: DailyWorkLog) -> DailyWorkLog:
        self.session.add(daily_work_log)
        self.session.flush()
        return daily_work_log

    def find_by_user_id_and_target_date(
        self,
        user_id: int,
        target_date: date,
    ) -> DailyWorkLog | None:
        stmt = select(DailyWorkLog).where(
            DailyWorkLog.user_id == user_id,
            DailyWorkLog.target_date == target_date,
        )
        return self.session.scalar(stmt)

    def find_all_by_user_id(self, user_id: int) -> list[DailyWorkLog]:
        stmt = (
            select(DailyWorkLog)
            .where(DailyWorkLog.user_id == user_id)
            .order_by(DailyWorkLog.target_date.desc())
        )
        return list(self.session.scalars(stmt).all())

    def delete_by_user_id_and_target_date(self, user_id: int, target_date: date) -> None:
        stmt = delete(DailyWorkLog).where(
            DailyWorkLog.user_id == user_id,
            DailyWorkLog.target_date == target_date,
        )
        self.session.execute(stmt)
        self.session.flush()
