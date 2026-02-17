import logging
import time
from datetime import date

from sqlalchemy.orm import Session

from dev_blackbox.client.slack_client import get_slack_client
from dev_blackbox.core.exception import (
    UserByIdNotFoundException,
    SlackUserNotAssignedException,
    NoSlackChannelsFound,
)
from dev_blackbox.storage.rds.entity import User
from dev_blackbox.storage.rds.entity.slack_message import SlackMessage
from dev_blackbox.storage.rds.repository import (
    UserRepository,
    SlackMessageRepository,
)
from dev_blackbox.util.datetime_util import get_daily_timestamp_range, get_yesterday

logger = logging.getLogger(__name__)


class SlackMessageService:

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.slack_message_repository = SlackMessageRepository(session)

    def get_slack_messages(
        self,
        user_id: int,
        target_date: date,
    ) -> list[SlackMessage]:
        return self.slack_message_repository.find_all_by_user_id_and_target_date(
            user_id,
            target_date,
        )

    def save_slack_messages(
        self,
        user_id: int,
        target_date: date | None = None,
    ) -> list[SlackMessage]:
        user = self._get_user_or_throw(user_id)
        target_date = target_date or get_yesterday(user.tz_info)
        slack_user = user.slack_user
        if not slack_user:
            raise SlackUserNotAssignedException(user_id)
        logger.info(f"Collecting Slack messages for user_id={user_id}, target_date={target_date}")

        # 기존 데이터 삭제 후 갱신
        self.slack_message_repository.delete_by_user_id_and_target_date(user_id, target_date)

        slack_client = get_slack_client()
        channels = slack_client.fetch_channels()
        if not channels:
            raise NoSlackChannelsFound()

        # target_date 타임스탬프 범위 (lookback 확장 시 필터링용)
        target_oldest, target_latest = get_daily_timestamp_range(target_date, user.tz_info)

        def _is_in_target_date(ts: str) -> bool:
            return float(target_oldest) <= float(ts) < float(target_latest)

        new_messages: list[SlackMessage] = []

        for channel in channels:
            time.sleep(1)  # Rate limit 대응
            messages = slack_client.fetch_messages_by_date(
                channel_id=channel.id,
                target_date=target_date,
                tz_info=user.tz_info,
                lookback_days=10,  # 과거 스레드 부모 메시지 포함을 위해 조회 범위 확장
            )

            messages_no_thread = [
                m
                for m in messages
                if m.thread_ts is None
                and m.user == slack_user.member_id
                and _is_in_target_date(m.ts)
            ]
            thread_parents = [
                m
                for m in messages
                if m.thread_ts is not None
                and (
                    _is_in_target_date(m.ts)
                    or (m.latest_reply and _is_in_target_date(m.latest_reply))
                )
            ]
            thread_ts_set = {m.thread_ts for m in thread_parents if m.thread_ts is not None}

            for msg in messages_no_thread:
                new_messages.append(
                    SlackMessage.create(
                        user_id=user_id,
                        slack_user_id=slack_user.id,
                        target_date=target_date,
                        channel_id=channel.id,
                        channel_name=channel.name,
                        message_ts=msg.ts,
                        message_text=msg.text,
                        message=msg.model_dump(mode="json"),
                        thread_ts=None,
                    )
                )

            # 스레드 답글: 사용자의 답글만 개별 row로 저장
            for thread_ts in thread_ts_set:
                time.sleep(2)  # Rate limit 대응
                thread_replies = slack_client.fetch_thread_replies(
                    channel_id=channel.id,
                    thread_ts=thread_ts,
                    target_date=target_date,
                    tz_info=user.tz_info,
                )
                user_replies = [r for r in thread_replies if r.user == slack_user.member_id]

                for reply in user_replies:
                    new_messages.append(
                        SlackMessage.create(
                            user_id=user_id,
                            slack_user_id=slack_user.id,
                            target_date=target_date,
                            channel_id=channel.id,
                            channel_name=channel.name,
                            message_ts=reply.ts,
                            message_text=reply.text,
                            message=reply.model_dump(mode="json"),
                            thread_ts=thread_ts,
                        )
                    )

        logger.info(
            f"Collected {len(new_messages)} Slack messages for user_id={user_id}, target_date={target_date}"
        )
        return self.slack_message_repository.save_all(new_messages)

    def _get_user_or_throw(self, user_id: int) -> User:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserByIdNotFoundException(user_id)
        return user
