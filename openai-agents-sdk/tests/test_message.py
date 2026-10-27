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

    @patch("listeners.events.message.review_message")
    def test_channel_thread_reply_is_reviewed_as_its_author(self, review_message):
        event = {
            "channel_type": "channel",
            "text": "Restarting the worker fixed it",
            "thread_ts": "1700000000.000100",
            "ts": "1700000000.000200",
        }

        self.handle(event)

        review_message.assert_called_once()
        kwargs = review_message.call_args.kwargs
        assert kwargs["channel_id"] == "C123"
        assert kwargs["event"] == event
        assert kwargs["user_id"] == "U123"
        assert kwargs["user_token"] == "xoxp-123"

    @patch("listeners.events.message.review_message")
    def test_top_level_channel_message_is_reviewed(self, review_message):
        self.handle(
            {
                "channel_type": "group",
                "text": "We decided to deploy on Tuesdays from now on",
                "ts": "1700000000.000100",
            }
        )

        review_message.assert_called_once()

    @patch("listeners.events.message.review_message")
    def test_broadcast_thread_reply_is_reviewed(self, review_message):
        self.handle(
            {
                "channel_type": "channel",
                "subtype": "thread_broadcast",
                "text": "Fixed: restarting the worker cleared the queue",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        review_message.assert_called_once()

    @patch("listeners.events.message.review_message")
    def test_message_without_user_token_is_not_reviewed(self, review_message):
        self.fake_context.user_token = None

        self.handle(
            {
                "channel_type": "channel",
                "text": "Restarting the worker fixed it",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        review_message.assert_not_called()

    @patch("listeners.events.message.review_message")
    def test_edited_message_is_not_reviewed(self, review_message):
        self.handle(
            {
                "channel_type": "channel",
                "subtype": "message_changed",
                "ts": "1700000000.000200",
            }
        )

        review_message.assert_not_called()

    @patch("listeners.events.message.review_message")
    def test_dm_is_not_reviewed(self, review_message):
        self.handle(
            {
                "channel_type": "im",
                "text": "Thanks!",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        review_message.assert_not_called()

    @patch("listeners.events.message.review_message")
    def test_bot_message_is_not_reviewed(self, review_message):
        self.handle(
            {
                "bot_id": "B123",
                "channel_type": "channel",
                "text": "Added the steps to the runbook.",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        review_message.assert_not_called()

    @patch("listeners.events.message.run_agent")
    def test_dm_without_user_token_asks_to_connect(self, run_agent):
        self.fake_context.user_token = None
        say = Mock()

        handle_message(
            client=self.fake_client,
            context=self.fake_context,
            event={"channel_type": "im", "text": "Hi", "ts": "1700000000.000100"},
            logger=test_logger,
            say=say,
            say_stream=Mock(),
            set_status=Mock(),
        )

        run_agent.assert_not_called()
        assert "Connect the Slack MCP Server" in say.call_args.kwargs["text"]
