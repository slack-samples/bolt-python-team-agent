import logging
from unittest.mock import Mock, patch

from slack_bolt import BoltContext
from slack_sdk import WebClient

from listeners.events.message import handle_message

test_logger = logging.getLogger(__name__)


class TestMessage:
    def setup_method(self):
        self.fake_client = Mock(WebClient)
        self.fake_context = Mock(BoltContext)
        self.fake_context.channel_id = "C123"
        self.fake_context.user_id = "U123"
        self.fake_context.user_token = "xoxp-123"

    def handle(self, event):
        handle_message(
            client=self.fake_client,
            context=self.fake_context,
            event=event,
            logger=test_logger,
            say=Mock(),
            say_stream=Mock(),
            set_status=Mock(),
        )

    @patch("listeners.events.message.suggest_when_settled")
    def test_channel_thread_reply_starts_a_runbook_check(self, suggest_when_settled):
        self.handle(
            {
                "channel_type": "channel",
                "text": "Restarting the worker fixed it",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        suggest_when_settled.assert_called_once()
        kwargs = suggest_when_settled.call_args.kwargs
        assert kwargs["channel_id"] == "C123"
        assert kwargs["thread_ts"] == "1700000000.000100"

    @patch("listeners.events.message.suggest_when_settled")
    def test_top_level_channel_message_is_not_checked(self, suggest_when_settled):
        self.handle(
            {
                "channel_type": "channel",
                "text": "Is anyone else seeing deploys fail?",
                "ts": "1700000000.000100",
            }
        )

        suggest_when_settled.assert_not_called()

    @patch("listeners.events.message.suggest_when_settled")
    def test_thread_reply_without_user_token_starts_a_runbook_check(
        self, suggest_when_settled
    ):
        self.fake_context.user_token = None

        self.handle(
            {
                "channel_type": "channel",
                "text": "Restarting the worker fixed it",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        suggest_when_settled.assert_called_once()

    @patch("listeners.events.message.suggest_when_settled")
    def test_broadcast_thread_reply_starts_a_runbook_check(self, suggest_when_settled):
        self.handle(
            {
                "channel_type": "channel",
                "subtype": "thread_broadcast",
                "text": "Fixed: restarting the worker cleared the queue",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        suggest_when_settled.assert_called_once()

    @patch("listeners.events.message.suggest_when_settled")
    def test_edited_thread_reply_is_not_checked(self, suggest_when_settled):
        self.handle(
            {
                "channel_type": "channel",
                "subtype": "message_changed",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        suggest_when_settled.assert_not_called()

    @patch("listeners.events.message.suggest_when_settled")
    def test_dm_thread_reply_is_not_checked(self, suggest_when_settled):
        self.handle(
            {
                "channel_type": "im",
                "text": "Thanks!",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        suggest_when_settled.assert_not_called()

    @patch("listeners.events.message.suggest_when_settled")
    def test_bot_reply_is_not_checked(self, suggest_when_settled):
        self.handle(
            {
                "bot_id": "B123",
                "channel_type": "channel",
                "text": "Added the steps to the runbook.",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        suggest_when_settled.assert_not_called()
