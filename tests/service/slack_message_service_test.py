from datetime import date
from typing import Callable
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from dev_blackbox.client.model.slack_api_model import SlackChannelModel, SlackMessageModel
from dev_blackbox.client.slack_client import SlackClient
from dev_blackbox.core.exception import (
    NoSlackChannelsFound,
    SlackUserNotAssignedException,
    UserNotFoundException,
)
from dev_blackbox.service.slack_message_service import SlackMessageService
from dev_blackbox.storage.rds.entity.slack_message import SlackMessage
from dev_blackbox.storage.rds.entity.slack_secret import SlackSecret
from dev_blackbox.storage.rds.entity.slack_user import SlackUser
from dev_blackbox.storage.rds.entity.user import User


class SlackMessageServiceTest:

    # ── get_slack_messages ──

    def test_get_slack_messages(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
        slack_message_fixture: Callable[..., SlackMessage],
    ):
        # given
        user = user_fixture()
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(slack_secret_id=secret.id, user_id=user.id)
        target_date = date(2025, 1, 1)
        message = slack_message_fixture(
            user_id=user.id,
            slack_user_id=slack_user.id,
            target_date=target_date,
        )

        service = SlackMessageService(db_session)

        # when
        result = service.get_slack_messages(user.id, target_date)

        # then
        assert result == [message]

    def test_get_slack_messages_메시지가_없으면_빈_리스트(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = SlackMessageService(db_session)

        # when
        result = service.get_slack_messages(user.id, date(2025, 1, 1))

        # then
        assert result == []

    def test_get_slack_messages_다른_날짜_메시지는_조회되지_않음(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
        slack_message_fixture: Callable[..., SlackMessage],
    ):
        # given
        user = user_fixture()
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(slack_secret_id=secret.id, user_id=user.id)
        slack_message_fixture(
            user_id=user.id,
            slack_user_id=slack_user.id,
            target_date=date(2025, 1, 2),
        )

        service = SlackMessageService(db_session)

        # when
        result = service.get_slack_messages(user.id, date(2025, 1, 1))

        # then
        assert result == []

    # ── save_slack_messages ──

    def test_save_slack_messages(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        user = user_fixture()
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(
            slack_secret_id=secret.id,
            user_id=user.id,
            member_id="U_MSG_TEST",
        )
        target_date = date(2025, 1, 1)

        # mock
        mock_channel = SlackChannelModel(id="C001", name="general", is_private=False)
        # 유저 타임존(Asia/Seoul) 기준 2025-01-01 00:00:00 ~ 23:59:59 → UTC 1735657200 ~ 1735743600
        mock_message = SlackMessageModel(
            ts="1735693200.000100",  # target_date 범위 내
            user="U_MSG_TEST",
            text="Hello World",
            thread_ts=None,
            latest_reply=None,
        )

        mock_client = MagicMock(spec=SlackClient)
        mock_client.fetch_channels.return_value = [mock_channel]
        mock_client.fetch_messages_by_date.return_value = [mock_message]

        mocker.patch.object(
            SlackMessageService,
            "_get_user_or_throw",
            return_value=user,
        )
        mocker.patch(
            "dev_blackbox.service.slack_message_service.SlackSecretService.get_slack_client",
            return_value=mock_client,
        )
        mocker.patch("dev_blackbox.service.slack_message_service.time.sleep")

        service = SlackMessageService(db_session)

        # when
        result = service.save_slack_messages(user.id, target_date)

        # then
        assert len(result) == 1
        assert result[0].message_text == "Hello World"
        assert result[0].channel_name == "general"
        assert result[0].thread_ts is None
        mock_client.fetch_channels.assert_called_once()

    def test_save_slack_messages_스레드_답글_포함(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        user = user_fixture()
        secret = slack_secret_fixture()
        slack_user = slack_user_fixture(
            slack_secret_id=secret.id,
            user_id=user.id,
            member_id="U_THREAD_TEST",
        )
        target_date = date(2025, 1, 1)

        # mock
        mock_channel = SlackChannelModel(id="C001", name="dev", is_private=False)
        # 스레드가 있는 메시지 (thread_ts != None, target_date 범위 내)
        mock_thread_message = SlackMessageModel(
            ts="1735693200.000200",
            user="U_OTHER",
            text="Thread parent",
            thread_ts="1735693200.000200",
            latest_reply="1735693200.000300",
        )

        mock_reply = SlackMessageModel(
            ts="1735693200.000300",
            user="U_THREAD_TEST",
            text="My reply",
            thread_ts="1735693200.000200",
        )

        mock_client = MagicMock(spec=SlackClient)
        mock_client.fetch_channels.return_value = [mock_channel]
        mock_client.fetch_messages_by_date.return_value = [mock_thread_message]
        mock_client.fetch_thread_replies.return_value = [mock_reply]

        mocker.patch.object(
            SlackMessageService,
            "_get_user_or_throw",
            return_value=user,
        )
        mocker.patch(
            "dev_blackbox.service.slack_message_service.SlackSecretService.get_slack_client",
            return_value=mock_client,
        )
        mocker.patch("dev_blackbox.service.slack_message_service.time.sleep")

        service = SlackMessageService(db_session)

        # when
        result = service.save_slack_messages(user.id, target_date)

        # then
        assert len(result) == 1
        assert result[0].message_text == "My reply"
        assert result[0].thread_ts == "1735693200.000200"
        mock_client.fetch_thread_replies.assert_called_once()

    def test_save_slack_messages_채널이_없으면_예외(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        user = user_fixture()
        secret = slack_secret_fixture()
        slack_user_fixture(
            slack_secret_id=secret.id,
            user_id=user.id,
            member_id="U_NO_CHANNEL",
        )
        target_date = date(2025, 1, 1)

        # mock
        mock_client = MagicMock(spec=SlackClient)
        mock_client.fetch_channels.return_value = []

        mocker.patch.object(
            SlackMessageService,
            "_get_user_or_throw",
            return_value=user,
        )
        mocker.patch(
            "dev_blackbox.service.slack_message_service.SlackSecretService.get_slack_client",
            return_value=mock_client,
        )

        service = SlackMessageService(db_session)

        # when & then
        with pytest.raises(NoSlackChannelsFound):
            service.save_slack_messages(user.id, target_date)

    def test_save_slack_messages_메시지가_없으면_빈_리스트(
        self,
        mocker,
        db_session: Session,
        user_fixture: Callable[..., User],
        slack_secret_fixture: Callable[..., SlackSecret],
        slack_user_fixture: Callable[..., SlackUser],
    ):
        # given
        user = user_fixture()
        secret = slack_secret_fixture()
        slack_user_fixture(
            slack_secret_id=secret.id,
            user_id=user.id,
            member_id="U_EMPTY_MSG",
        )
        target_date = date(2025, 1, 1)

        # mock
        mock_channel = SlackChannelModel(id="C001", name="general", is_private=False)

        mock_client = MagicMock(spec=SlackClient)
        mock_client.fetch_channels.return_value = [mock_channel]
        mock_client.fetch_messages_by_date.return_value = []

        mocker.patch.object(
            SlackMessageService,
            "_get_user_or_throw",
            return_value=user,
        )
        mocker.patch(
            "dev_blackbox.service.slack_message_service.SlackSecretService.get_slack_client",
            return_value=mock_client,
        )
        mocker.patch("dev_blackbox.service.slack_message_service.time.sleep")

        service = SlackMessageService(db_session)

        # when
        result = service.save_slack_messages(user.id, target_date)

        # then
        assert result == []

    # ── save_slack_messages 예외 케이스 ──

    def test_save_slack_messages_사용자가_없으면_예외(
        self,
        db_session: Session,
    ):
        # given
        service = SlackMessageService(db_session)

        # when & then
        with pytest.raises(UserNotFoundException):
            service.save_slack_messages(9999, date(2025, 1, 1))

    def test_save_slack_messages_slack_user가_없으면_예외(
        self,
        db_session: Session,
        user_fixture: Callable[..., User],
    ):
        # given
        user = user_fixture()
        service = SlackMessageService(db_session)

        # when & then
        with pytest.raises(SlackUserNotAssignedException):
            service.save_slack_messages(user.id, date(2025, 1, 1))
