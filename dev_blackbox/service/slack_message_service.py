import logging
import time
from datetime import date

from sqlalchemy.orm import Session

from dev_blackbox.client.model.slack_api_model import SlackMessageModel
from dev_blackbox.client.slack_client import get_slack_client
from dev_blackbox.core.exception import (
    UserByIdNotFoundException,
    SlackUserNotAssignedException,
)
from dev_blackbox.storage.rds.entity.slack_message import SlackMessage
from dev_blackbox.storage.rds.repository import (
    UserRepository,
    SlackUserRepository,
    SlackMessageRepository,
)
from dev_blackbox.util.datetime_util import get_yesterday

logger = logging.getLogger(__name__)


class SlackMessageService:

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.slack_user_repository = SlackUserRepository(session)
        self.slack_message_repository = SlackMessageRepository(session)

    def get_slack_messages(
        self,
        user_id: int,
        target_date: date,
    ) -> list[SlackMessage]:
        return self.slack_message_repository.find_all_by_user_id_and_target_date(
            user_id, target_date
        )

    def save_slack_messages(
        self,
        user_id: int,
        target_date: date | None = None,
    ) -> list[SlackMessage]:
        user = self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserByIdNotFoundException(user_id)

        if target_date is None:
            target_date = get_yesterday(user.tz_info)

        slack_user = self.slack_user_repository.find_by_user_id(user_id)
        if not slack_user:
            raise SlackUserNotAssignedException(user_id)

        # 기존 데이터 삭제 후 갱신 (멱등성 보장)
        self.slack_message_repository.delete_by_user_id_and_target_date(user_id, target_date)

        slack_client = get_slack_client()
        channels = slack_client.fetch_channels()

        all_messages: list[SlackMessage] = []

        for channel in channels:
            # 채널별 메시지 수집
            messages = slack_client.fetch_messages_by_date(
                channel_id=channel.id,
                target_date=target_date,
                tz_info=user.tz_info,
            )

            # 해당 Slack 사용자의 메시지만 필터링
            user_messages = [m for m in messages if m.user == slack_user.member_id]

            # 사용자가 참여한 스레드의 부모 ts 수집 (중복 제거)
            # 사용자가 직접 작성한 메시지 중 스레드에 속한 것만 대상
            thread_parent_ts_set: set[str] = {
                m.thread_ts for m in user_messages if m.thread_ts and m.thread_ts != m.ts
            }

            # 스레드 답글 수집
            thread_replies: list[SlackMessageModel] = []
            for thread_ts in thread_parent_ts_set:
                replies = slack_client.fetch_thread_replies(
                    channel_id=channel.id,
                    thread_ts=thread_ts,
                    target_date=target_date,
                    tz_info=user.tz_info,
                )
                thread_replies.extend([r for r in replies if r.user == slack_user.member_id])
                time.sleep(1)  # Rate limit 대응

            # 이미 수집된 채널 메시지와 중복되지 않는 스레드 답글만 추가
            collected_ts = {m.ts for m in user_messages}
            for reply in thread_replies:
                if reply.ts not in collected_ts:
                    user_messages.append(reply)
                    collected_ts.add(reply.ts)

            for msg in user_messages:
                all_messages.append(
                    SlackMessage.create(
                        user_id=user_id,
                        slack_user_id=slack_user.id,
                        target_date=target_date,
                        channel_id=channel.id,
                        channel_name=channel.name,
                        message_ts=msg.ts,
                        message_text=msg.text,
                        message=msg.model_dump(mode="json"),
                        thread_ts=msg.thread_ts,
                    )
                )

            time.sleep(1)  # Rate limit 대응 (채널 간)

        logger.info(
            f"Collected {len(all_messages)} Slack messages "
            f"for user_id={user_id}, target_date={target_date}"
        )

        if not all_messages:
            return []

        return self.slack_message_repository.save_all(all_messages)
