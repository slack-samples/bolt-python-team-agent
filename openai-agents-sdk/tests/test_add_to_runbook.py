import logging
from unittest.mock import Mock, patch

from slack_bolt import BoltContext
from slack_sdk import WebClient

from agent import RunbookUpdate
from agent.runbook_agent import build_runbook_input
from listeners.actions.add_to_runbook import handle_add_to_runbook

test_logger = logging.getLogger(__name__)

BODY = {
    "actions": [
        {"action_id": "add_to_runbook", "value": "Rotating the signing secret"}
    ],
    "message": {"ts": "1700000000.000300", "thread_ts": "1700000000.000100"},
}


class TestAddToRunbook:
    def setup_method(self):
        self.fake_ack = Mock()
        self.fake_client = Mock(WebClient)
        self.fake_client.chat_getPermalink.return_value = {
            "permalink": "https://example.slack.com/archives/C123/p1700000000000100"
        }
        self.fake_context = Mock(BoltContext)
        self.fake_context.channel_id = "C123"
        self.fake_context.user_id = "U123"
        self.fake_context.user_token = "xoxp-123"

    def click(self):
        handle_add_to_runbook(
            ack=self.fake_ack,
            body=BODY,
            client=self.fake_client,
            context=self.fake_context,
            logger=test_logger,
        )

    @patch("listeners.actions.add_to_runbook.save_to_runbook")
    def test_saves_the_thread_as_the_person_who_clicked(self, save_to_runbook):
        save_to_runbook.return_value = RunbookUpdate(
            changed=True,
            note="Added the rotation steps to [Runbook: Deploys](https://example.com).",
        )

        self.click()

        self.fake_ack.assert_called_once()
        kwargs = save_to_runbook.call_args.kwargs
        assert kwargs["thread_ts"] == "1700000000.000100"
        assert kwargs["topic"] == "Rotating the signing secret"
        assert kwargs["user_token"] == "xoxp-123"
        final = self.fake_client.chat_update.call_args_list[-1].kwargs
        assert final["ts"] == "1700000000.000300"
        assert "Runbook: Deploys" in final["markdown_text"]

    @patch("listeners.actions.add_to_runbook.save_to_runbook")
    def test_keeps_the_button_when_nothing_changed(self, save_to_runbook):
        save_to_runbook.return_value = RunbookUpdate(
            changed=False,
            note="I used all 50 steps I get before finishing the runbook.",
        )

        self.click()

        final = self.fake_client.chat_update.call_args_list[-1].kwargs
        action_ids = [
            element.action_id
            for block in final["blocks"]
            for element in getattr(block, "elements", [])
        ]
        assert "add_to_runbook" in action_ids
        ephemeral = self.fake_client.chat_postEphemeral.call_args.kwargs
        assert "50 steps" in ephemeral["markdown_text"]

    @patch("listeners.actions.add_to_runbook.save_to_runbook")
    def test_asks_to_connect_without_a_user_token(self, save_to_runbook):
        self.fake_context.user_token = None

        self.click()

        save_to_runbook.assert_not_called()
        self.fake_client.chat_update.assert_not_called()
        self.fake_client.chat_postEphemeral.assert_called_once()
        assert (
            "Connect the Slack MCP Server"
            in (self.fake_client.chat_postEphemeral.call_args.kwargs["text"])
        )

    @patch("listeners.actions.add_to_runbook.save_to_runbook")
    def test_restores_the_button_when_saving_fails(self, save_to_runbook, caplog):
        save_to_runbook.side_effect = Exception("test exception")

        self.click()

        final = self.fake_client.chat_update.call_args_list[-1].kwargs
        action_ids = [
            element.action_id
            for block in final["blocks"]
            for element in getattr(block, "elements", [])
        ]
        assert "add_to_runbook" in action_ids
        self.fake_client.chat_postEphemeral.assert_called_once()
        assert "test exception" in caplog.text


def test_build_runbook_input_points_at_the_thread():
    runbook_input = build_runbook_input(
        channel_id="C123",
        thread_ts="1700000000.000100",
        permalink="https://example.slack.com/archives/C123/p1700000000000100",
        topic="Rotating the signing secret",
    )

    assert "Rotating the signing secret" in runbook_input
    assert "C123" in runbook_input
    assert "1700000000.000100" in runbook_input
    assert "https://example.slack.com/archives/C123/p1700000000000100" in runbook_input
