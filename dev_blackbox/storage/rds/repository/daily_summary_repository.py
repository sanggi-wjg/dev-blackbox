from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from dev_blackbox.storage.rds.entity.daily_summary import DailySummary


class DailySummaryRepository:

    def __init__(self, session: Session):
        self.session = session

    def save(self, daily_summary: DailySummary) -> DailySummary:
        self.session.add(daily_summary)
        self.session.flush()
        return daily_summary

    def find_by_user_id_and_target_date(
        self, user_id: int, target_date: date
    ) -> DailySummary | None:
        stmt = select(DailySummary).where(
            DailySummary.user_id == user_id,
            DailySummary.target_date == target_date,
        )
        return self.session.scalar(stmt)

    def find_all_by_user_id(self, user_id: int) -> list[DailySummary]:
        stmt = (
            select(DailySummary)
            .where(DailySummary.user_id == user_id)
            .order_by(DailySummary.target_date.desc())
        )
        return list(self.session.scalars(stmt).all())

    def delete_by_user_id_and_target_date(self, user_id: int, target_date: date) -> None:
        stmt = delete(DailySummary).where(
            DailySummary.user_id == user_id,
            DailySummary.target_date == target_date,
        )
        self.session.execute(stmt)
        self.session.flush()
