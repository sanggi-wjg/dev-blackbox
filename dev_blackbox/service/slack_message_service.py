import logging
import time
from datetime import date

from sqlalchemy.orm import Session

from dev_blackbox.client.model.slack_api_model import SlackMessageModel
from dev_blackbox.client.slack_client import get_slack_client
from dev_blackbox.core.exception import (
    UserNotFoundException,
    SlackUserNotAssignedException,
    NoSlackChannelsFound,
)
from dev_blackbox.storage.rds.entity import User
from dev_blackbox.storage.rds.entity.slack_message import SlackMessage
from dev_blackbox.storage.rds.repository import (
    UserRepository,
    SlackMessageRepository,
)
from dev_blackbox.util.datetime_util import (
    get_daily_timestamp_range,
    get_yesterday,
    is_timestamp_in_range,
)

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

        target_oldest, target_latest = get_daily_timestamp_range(target_date, user.tz_info)
        new_messages: list[SlackMessage] = []

        for channel in channels:
            messages = slack_client.fetch_messages_by_date(
                channel_id=channel.id,
                target_date=target_date,
                tz_info=user.tz_info,
                lookback_days=15,  # 과거 스레드 부모 메시지 포함을 위해서 과거도 같이 조회 하도록 (15일 정도면...??)
            )

            # 유저 메시지 중 스레드 없는 메시지 / 스레드 있는 메시지 구분
            messages_no_thread = self._filter_message_no_thread(
                messages, slack_user.member_id, target_oldest, target_latest
            )
            messages_with_thread = self._filter_message_with_thread(
                messages, target_oldest, target_latest
            )
            thread_ts_set = {m.thread_ts for m in messages_with_thread if m.thread_ts is not None}
            logger.info(f"Collected {len(messages_no_thread)} Slack messages without thread.")
            logger.info(f"Collected {len(messages_with_thread)} Slack messages with thread.")

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
                time.sleep(2)  # rate limit
            time.sleep(2)  # rate limit
        logger.info(
            f"Collected {len(new_messages)} Slack messages for user_id={user_id}, target_date={target_date}"
        )
        return self.slack_message_repository.save_all(new_messages)

    def _get_user_or_throw(self, user_id: int) -> User:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)
        return user

    def _filter_message_no_thread(
        self,
        messages: list[SlackMessageModel],
        slack_member_id: str,
        target_oldest: float,
        target_latest: float,
    ) -> list[SlackMessageModel]:
        return [
            m
            for m in messages
            if m.thread_ts is None
            and m.user == slack_member_id
            and is_timestamp_in_range(m.ts, target_oldest, target_latest)
        ]

    def _filter_message_with_thread(
        self,
        messages: list[SlackMessageModel],
        target_oldest: float,
        target_latest: float,
    ) -> list[SlackMessageModel]:
        return [
            m
            for m in messages
            if m.thread_ts is not None
            and (
                is_timestamp_in_range(m.ts, target_oldest, target_latest)
                or (
                    m.latest_reply
                    and is_timestamp_in_range(m.latest_reply, target_oldest, target_latest)
                )
            )
        ]
