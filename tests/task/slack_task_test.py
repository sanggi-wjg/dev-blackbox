from unittest.mock import MagicMock, patch

from dev_blackbox.task.slack_task import sync_slack_users_task
from tests.fixtures.lock_helper import mock_lock_acquired, mock_lock_not_acquired


class SlackTaskTest:

    def test_sync_slack_users_task_락_획득_시_동기화를_실행한다(self):
        # given
        mock_service = MagicMock()

        with (
            patch(
                "dev_blackbox.task.slack_task.distributed_lock",
                return_value=mock_lock_acquired(),
            ),
            patch("dev_blackbox.task.slack_task.SlackUserService", return_value=mock_service),
            patch("dev_blackbox.task.slack_task.get_db_session") as mock_db,
        ):
            mock_db.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            # when
            sync_slack_users_task()

        # then
        mock_service.sync_all_slack_users.assert_called_once()

    def test_sync_slack_users_task_락_미획득_시_동기화를_실행하지_않는다(self):
        # given
        mock_service = MagicMock()

        with (
            patch(
                "dev_blackbox.task.slack_task.distributed_lock",
                return_value=mock_lock_not_acquired(),
            ),
            patch("dev_blackbox.task.slack_task.SlackUserService", return_value=mock_service),
        ):
            # when
            sync_slack_users_task()

        # then
        mock_service.sync_all_slack_users.assert_not_called()
