import logging
from unittest.mock import Mock, patch

from slack_sdk import WebClient

from agent import RunbookCheck
from runbooks.suggest import build_transcript, suggest_runbook

test_logger = logging.getLogger(__name__)

THREAD = [
    {
        "user": "U123",
        "text": "Deploys are failing with a 401",
        "ts": "1700000000.000100",
    },
    {
        "user": "U456",
        "text": "Rotate the signing secret, then redeploy",
        "ts": "1700000000.000200",
    },
    {
        "bot_id": "B123",
        "text": "Added the steps to the runbook.",
        "ts": "1700000000.000300",
    },
]


def test_build_transcript_names_who_said_what():
    transcript = build_transcript(THREAD)

    assert transcript.splitlines() == [
        "<@U123>: Deploys are failing with a 401",
        "<@U456>: Rotate the signing secret, then redeploy",
        "agent: Added the steps to the runbook.",
    ]


class TestSuggestRunbook:
    def setup_method(self):
        self.fake_client = Mock(WebClient)
        self.fake_client.conversations_replies.return_value = {"messages": THREAD}

    def suggest(self):
        suggest_runbook(
            client=self.fake_client,
            channel_id="C123",
            thread_ts="1700000000.000100",
            logger=test_logger,
        )

    @patch("runbooks.suggest.check_thread")
    def test_offers_a_runbook_when_the_thread_settled_something(self, check_thread):
        check_thread.return_value = RunbookCheck(
            worth_saving=True, topic="Rotating the signing secret"
        )

        self.suggest()

        assert "Rotate the signing secret" in check_thread.call_args.args[0]
        self.fake_client.chat_postMessage.assert_called_once()
        kwargs = self.fake_client.chat_postMessage.call_args.kwargs
        assert kwargs["channel"] == "C123"
        assert kwargs["thread_ts"] == "1700000000.000100"
        action_ids = [
            element.action_id
            for block in kwargs["blocks"]
            for element in getattr(block, "elements", [])
        ]
        assert "add_to_runbook" in action_ids

    @patch("runbooks.suggest.check_thread")
    def test_stays_quiet_when_nothing_settled(self, check_thread):
        check_thread.return_value = RunbookCheck(worth_saving=False, topic="")

        self.suggest()

        self.fake_client.chat_postMessage.assert_not_called()

    @patch("runbooks.suggest.check_thread")
    def test_logs_check_errors(self, check_thread, caplog):
        check_thread.side_effect = Exception("test exception")

        self.suggest()

        self.fake_client.chat_postMessage.assert_not_called()
        assert "test exception" in caplog.text
