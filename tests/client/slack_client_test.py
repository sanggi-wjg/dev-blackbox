from datetime import date
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from dev_blackbox.client.model.slack_api_model import SlackChannelModel, SlackMessageModel
from dev_blackbox.client.slack_client import SlackClient
from dev_blackbox.core.exception import SlackClientException
from dev_blackbox.util.datetime_util import get_daily_timestamp_range


class SlackClientTest:
    KST = ZoneInfo("Asia/Seoul")
    TARGET_DATE = date(2025, 1, 15)

    def setup_method(self):
        self.mock_web_client = MagicMock()
        self.slack_client = SlackClient("xoxb-test-token")
        self.slack_client.client = self.mock_web_client

    def test_fetch_users_일반_사용자만_반환한다(self):
        # given
        self.mock_web_client.users_list.return_value = {
            "ok": True,
            "members": [
                {"id": "U001", "name": "alice", "is_bot": False},
                {"id": "U002", "name": "bot-user", "is_bot": True},
                {"id": "USLACKBOT", "name": "slackbot", "is_bot": False},
                {"id": "U003", "name": "bob", "is_bot": False},
            ],
        }

        # when
        result = self.slack_client.fetch_users()

        # then
        assert len(result) == 2
        assert result[0]["id"] == "U001"
        assert result[1]["id"] == "U003"

    def test_fetch_users_filter_bot이_False면_모든_사용자를_반환한다(self):
        # given
        self.mock_web_client.users_list.return_value = {
            "ok": True,
            "members": [
                {"id": "U001", "name": "alice", "is_bot": False},
                {"id": "U002", "name": "bot-user", "is_bot": True},
                {"id": "USLACKBOT", "name": "slackbot", "is_bot": False},
            ],
        }

        # when
        result = self.slack_client.fetch_users(filter_bot=False)

        # then
        assert len(result) == 3

    def test_fetch_users_API_응답이_실패하면_SlackClientException이_발생한다(self):
        # given
        self.mock_web_client.users_list.return_value = {"ok": False, "error": "invalid_auth"}

        # when & then
        with pytest.raises(SlackClientException):
            self.slack_client.fetch_users()

    def test_fetch_users_members가_비어있으면_빈_리스트를_반환한다(self):
        # given
        self.mock_web_client.users_list.return_value = {"ok": True, "members": []}

        # when
        result = self.slack_client.fetch_users()

        # then
        assert result == []

    def test_fetch_channels_봇이_참여한_채널만_반환한다(self):
        # given
        self.mock_web_client.conversations_list.return_value = {
            "channels": [
                {"id": "C001", "name": "general", "is_member": True, "is_private": False},
                {"id": "C002", "name": "random", "is_member": False, "is_private": False},
                {"id": "C003", "name": "secret", "is_member": True, "is_private": True},
            ],
            "response_metadata": {"next_cursor": ""},
        }

        # when
        result = self.slack_client.fetch_channels()

        # then
        assert len(result) == 2
        assert result[0] == SlackChannelModel(id="C001", name="general", is_private=False)
        assert result[1] == SlackChannelModel(id="C003", name="secret", is_private=True)

    def test_fetch_channels_페이지네이션으로_여러_페이지를_조회한다(self):
        # given
        self.mock_web_client.conversations_list.side_effect = [
            {
                "channels": [
                    {"id": "C001", "name": "general", "is_member": True, "is_private": False},
                ],
                "response_metadata": {"next_cursor": "cursor_page2"},
            },
            {
                "channels": [
                    {"id": "C002", "name": "dev", "is_member": True, "is_private": False},
                ],
                "response_metadata": {"next_cursor": ""},
            },
        ]

        # when
        result = self.slack_client.fetch_channels()

        # then
        assert len(result) == 2
        assert result[0].id == "C001"
        assert result[1].id == "C002"
        assert self.mock_web_client.conversations_list.call_count == 2

    def test_fetch_channels_채널이_없으면_빈_리스트를_반환한다(self):
        # given
        self.mock_web_client.conversations_list.return_value = {
            "channels": [],
            "response_metadata": {"next_cursor": ""},
        }

        # when
        result = self.slack_client.fetch_channels()

        # then
        assert result == []

    def test_fetch_messages_by_date_일반_메시지만_반환한다(self):
        # given
        self.mock_web_client.conversations_history.return_value = {
            "messages": [
                {"ts": "1736899200.001", "user": "U001", "text": "hello"},
                {
                    "ts": "1736899200.002",
                    "user": "U001",
                    "text": "joined",
                    "subtype": "channel_join",
                },
                {"ts": "1736899200.003", "user": "U002", "text": "world"},
            ],
            "has_more": False,
        }

        # when
        result = self.slack_client.fetch_messages_by_date("C001", self.TARGET_DATE, self.KST)

        # then
        assert len(result) == 2
        assert result[0] == SlackMessageModel(ts="1736899200.001", user="U001", text="hello")
        assert result[1] == SlackMessageModel(ts="1736899200.003", user="U002", text="world")

    def test_fetch_messages_by_date_스레드_메시지의_thread_ts와_latest_reply를_포함한다(self):
        # given
        self.mock_web_client.conversations_history.return_value = {
            "messages": [
                {
                    "ts": "1736899200.001",
                    "user": "U001",
                    "text": "thread parent",
                    "thread_ts": "1736899200.001",
                    "latest_reply": "1736899200.099",
                },
            ],
            "has_more": False,
        }

        # when
        result = self.slack_client.fetch_messages_by_date("C001", self.TARGET_DATE, self.KST)

        # then
        assert len(result) == 1
        assert result[0].thread_ts == "1736899200.001"
        assert result[0].latest_reply == "1736899200.099"

    def test_fetch_messages_by_date_lookback_days가_적용되면_oldest가_확장된다(self):
        # given
        self.mock_web_client.conversations_history.return_value = {
            "messages": [],
            "has_more": False,
        }

        # when
        self.slack_client.fetch_messages_by_date(
            "C001", self.TARGET_DATE, self.KST, lookback_days=3
        )

        # then
        call_kwargs = self.mock_web_client.conversations_history.call_args.kwargs
        oldest_without_lookback = str(get_daily_timestamp_range(self.TARGET_DATE, self.KST)[0])
        assert float(call_kwargs["oldest"]) < float(oldest_without_lookback)

    def test_fetch_messages_by_date_페이지네이션으로_여러_페이지를_조회한다(self):
        # given
        self.mock_web_client.conversations_history.side_effect = [
            {
                "messages": [{"ts": "1736899200.001", "user": "U001", "text": "page1"}],
                "has_more": True,
                "response_metadata": {"next_cursor": "cursor_page2"},
            },
            {
                "messages": [{"ts": "1736899200.002", "user": "U002", "text": "page2"}],
                "has_more": False,
            },
        ]

        # when
        result = self.slack_client.fetch_messages_by_date("C001", self.TARGET_DATE, self.KST)

        # then
        assert len(result) == 2
        assert self.mock_web_client.conversations_history.call_count == 2

    def test_fetch_messages_by_date_메시지가_없으면_빈_리스트를_반환한다(self):
        # given
        self.mock_web_client.conversations_history.return_value = {
            "messages": [],
            "has_more": False,
        }

        # when
        result = self.slack_client.fetch_messages_by_date("C001", self.TARGET_DATE, self.KST)

        # then
        assert result == []

    def test_fetch_thread_replies_부모_메시지를_제외하고_답글만_반환한다(self):
        # given
        thread_ts = "1736899200.001"
        self.mock_web_client.conversations_replies.return_value = {
            "messages": [
                {"ts": thread_ts, "user": "U001", "text": "parent", "thread_ts": thread_ts},
                {"ts": "1736899200.002", "user": "U002", "text": "reply1", "thread_ts": thread_ts},
                {"ts": "1736899200.003", "user": "U003", "text": "reply2", "thread_ts": thread_ts},
            ],
            "has_more": False,
        }

        # when
        result = self.slack_client.fetch_thread_replies(
            "C001", thread_ts, self.TARGET_DATE, self.KST
        )

        # then
        assert len(result) == 2
        assert result[0].text == "reply1"
        assert result[1].text == "reply2"

    def test_fetch_thread_replies_include_parent가_True면_부모_메시지도_포함한다(self):
        # given
        thread_ts = "1736899200.001"
        self.mock_web_client.conversations_replies.return_value = {
            "messages": [
                {"ts": thread_ts, "user": "U001", "text": "parent", "thread_ts": thread_ts},
                {"ts": "1736899200.002", "user": "U002", "text": "reply1", "thread_ts": thread_ts},
            ],
            "has_more": False,
        }

        # when
        result = self.slack_client.fetch_thread_replies(
            "C001", thread_ts, self.TARGET_DATE, self.KST, include_parent=True
        )

        # then
        assert len(result) == 2
        assert result[0].text == "parent"
        assert result[1].text == "reply1"

    def test_fetch_thread_replies_subtype이_있는_시스템_메시지는_제외한다(self):
        # given
        thread_ts = "1736899200.001"
        self.mock_web_client.conversations_replies.return_value = {
            "messages": [
                {"ts": thread_ts, "user": "U001", "text": "parent", "thread_ts": thread_ts},
                {"ts": "1736899200.002", "user": "U002", "text": "reply", "thread_ts": thread_ts},
                {
                    "ts": "1736899200.003",
                    "user": "U003",
                    "text": "pinned",
                    "thread_ts": thread_ts,
                    "subtype": "channel_join",
                },
            ],
            "has_more": False,
        }

        # when
        result = self.slack_client.fetch_thread_replies(
            "C001", thread_ts, self.TARGET_DATE, self.KST
        )

        # then
        assert len(result) == 1
        assert result[0].text == "reply"

    def test_fetch_thread_replies_페이지네이션으로_여러_페이지를_조회한다(self):
        # given
        thread_ts = "1736899200.001"
        self.mock_web_client.conversations_replies.side_effect = [
            {
                "messages": [
                    {"ts": thread_ts, "user": "U001", "text": "parent", "thread_ts": thread_ts},
                    {"ts": "1736899200.002", "user": "U002", "text": "r1", "thread_ts": thread_ts},
                ],
                "has_more": True,
                "response_metadata": {"next_cursor": "cursor_page2"},
            },
            {
                "messages": [
                    {"ts": "1736899200.003", "user": "U003", "text": "r2", "thread_ts": thread_ts},
                ],
                "has_more": False,
            },
        ]

        # when
        result = self.slack_client.fetch_thread_replies(
            "C001", thread_ts, self.TARGET_DATE, self.KST
        )

        # then
        assert len(result) == 2
        assert result[0].text == "r1"
        assert result[1].text == "r2"
        assert self.mock_web_client.conversations_replies.call_count == 2

    def test_fetch_thread_replies_답글이_없으면_빈_리스트를_반환한다(self):
        # given
        thread_ts = "1736899200.001"
        self.mock_web_client.conversations_replies.return_value = {
            "messages": [
                {"ts": thread_ts, "user": "U001", "text": "parent", "thread_ts": thread_ts},
            ],
            "has_more": False,
        }

        # when
        result = self.slack_client.fetch_thread_replies(
            "C001", thread_ts, self.TARGET_DATE, self.KST
        )

        # then
        assert result == []
