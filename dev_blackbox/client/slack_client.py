import logging
from datetime import date, timedelta
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

from slack_sdk import WebClient

from dev_blackbox.client.model.slack_api_model import SlackChannelModel, SlackMessageModel
from dev_blackbox.core.config import get_settings
from dev_blackbox.core.exception import SlackClientException
from dev_blackbox.util.datetime_util import get_daily_timestamp_range

logger = logging.getLogger(__name__)


class SlackClient:

    def __init__(self, bot_token: str):
        self.client = WebClient(token=bot_token)

    @classmethod
    def create(cls, bot_token: str) -> "SlackClient":
        logger.debug("Creating SlackClient")
        return cls(bot_token)

    def fetch_users(self, filter_bot: bool = True) -> list[dict[str, Any]]:
        logger.debug("Fetching users")

        response = self.client.users_list()
        if not response.get("ok"):
            raise SlackClientException(f"Failed to fetch users: {response}")

        users = response.get("members", [])
        if filter_bot:
            return [
                user for user in users if not user.get("is_bot") and user.get("id") != "USLACKBOT"
            ]
        return users

    def fetch_channels(self) -> list[SlackChannelModel]:
        """
        봇이 참여한 채널 목록 조회
        """
        channels: list[SlackChannelModel] = []
        cursor = None

        while True:
            response = self.client.conversations_list(
                types="public_channel,private_channel",
                exclude_archived=True,
                limit=200,
                cursor=cursor,
            )
            for ch in response.get("channels", []):
                if ch.get("is_member", False):
                    channels.append(
                        SlackChannelModel(
                            id=ch["id"],
                            name=ch["name"],
                            is_private=ch.get("is_private", False),
                        )
                    )

            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        logger.info(f"Fetched {len(channels)} channels")
        return channels

    def fetch_messages_by_date(
        self,
        channel_id: str,
        target_date: date,
        tz_info: ZoneInfo,
        lookback_days: int = 0,
    ) -> list[SlackMessageModel]:
        """
        특정 채널에서 메시지 조회.
        lookback_days > 0이면 oldest를 target_date - lookback_days로 확장하여
        과거 스레드 부모 메시지도 포함.
        """
        oldest, latest = get_daily_timestamp_range(target_date, tz_info)
        if lookback_days > 0:
            oldest, _ = get_daily_timestamp_range(
                target_date - timedelta(days=lookback_days), tz_info
            )

        messages: list[SlackMessageModel] = []
        cursor = None

        while True:
            response = self.client.conversations_history(
                channel=channel_id,
                oldest=str(oldest),
                latest=str(latest),
                limit=200,
                cursor=cursor,
            )
            logger.debug(f"Fetched {len(response.get('messages', []))} messages")

            for msg in response.get("messages", []):
                if msg.get("subtype") is None:
                    messages.append(
                        SlackMessageModel(
                            ts=msg["ts"],
                            user=msg.get("user", ""),
                            text=msg.get("text", ""),
                            thread_ts=msg.get("thread_ts"),
                            latest_reply=msg.get("latest_reply"),
                        )
                    )

            if not response.get("has_more", False):
                break
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        logger.info(f"Fetched {len(messages)} messages")
        return messages

    def fetch_thread_replies(
        self,
        channel_id: str,
        thread_ts: str,
        target_date: date,
        tz_info: ZoneInfo,
        include_parent: bool = False,
    ) -> list[SlackMessageModel]:
        """스레드 답글 조회 (target_date 범위만)"""
        oldest, latest = get_daily_timestamp_range(target_date, tz_info)
        replies: list[SlackMessageModel] = []
        cursor = None

        while True:
            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                oldest=str(oldest),
                latest=str(latest),
                limit=100,
                cursor=cursor,
            )
            logger.debug(f"Fetched {len(response.get('messages', []))} replies")

            for msg in response.get("messages", []):
                if not include_parent and msg.get("ts") == thread_ts:
                    continue
                if msg.get("subtype") is None:
                    replies.append(
                        SlackMessageModel(
                            ts=msg["ts"],
                            user=msg.get("user", ""),
                            text=msg.get("text", ""),
                            thread_ts=msg.get("thread_ts"),
                        )
                    )

            if not response.get("has_more", False):
                break
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        logger.info(f"Fetched {len(replies)} replies")
        return replies


@lru_cache
def get_slack_client() -> SlackClient:
    slack_secrets = get_settings().slack
    return SlackClient.create(bot_token=slack_secrets.bot_token)
