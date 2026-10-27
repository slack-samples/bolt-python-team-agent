import logging
from unittest.mock import Mock, patch

from agents import RunResult, ToolCallItem
from slack_sdk import WebClient

from runbooks.review import build_review_input, changed_a_runbook, review_settled_thread

test_logger = logging.getLogger(__name__)

THREAD = [
    {"user": "U123", "text": "Deploys are failing with a 401"},
    {"user": "U456", "text": "Rotate the signing secret, then redeploy"},
    {"bot_id": "B123", "text": "Here's what I found."},
]


def run_result(
    *tool_names,
    final_output="Added the steps to [Runbook: Deploys](https://example.com).",
):
    result = Mock(RunResult)
    result.final_output = final_output
    items = []
    for name in tool_names:
        item = Mock(ToolCallItem)
        item.raw_item = Mock(spec=["name"])
        item.raw_item.name = name
        items.append(item)
    result.new_items = items
    return result


def test_build_review_input_names_who_said_what():
    review_input = build_review_input(
        THREAD, "https://example.slack.com/archives/C123/p1"
    )

    assert "Link: https://example.slack.com/archives/C123/p1" in review_input
    assert "<@U123>: Deploys are failing with a 401" in review_input
    assert "<@U456>: Rotate the signing secret, then redeploy" in review_input
    assert "agent: Here's what I found." in review_input


def test_changed_a_runbook_looks_for_canvas_writes():
    assert changed_a_runbook(
        run_result("slack_search_public_and_private", "slack_update_canvas")
    )
    assert changed_a_runbook(run_result("slack_create_canvas"))
    assert not changed_a_runbook(
        run_result("slack_search_public_and_private", "slack_read_canvas")
    )


class TestReviewSettledThread:
    def setup_method(self):
        self.fake_client = Mock(WebClient)
        self.fake_client.conversations_replies.return_value = {"messages": THREAD}
        self.fake_client.chat_getPermalink.return_value = {
            "permalink": "https://example.slack.com/archives/C123/p1700000000000100"
        }

    def review(self):
        review_settled_thread(
            client=self.fake_client,
            channel_id="C123",
            thread_ts="1700000000.000100",
            user_id="U456",
            user_token="xoxp-456",
            logger=test_logger,
        )

    @patch("runbooks.review.review_thread")
    def test_tells_the_person_it_ran_as_when_a_runbook_changed(self, review_thread):
        review_thread.return_value = run_result("slack_update_canvas")

        self.review()

        review_input, deps = review_thread.call_args.args
        assert "Rotate the signing secret" in review_input
        assert deps.user_id == "U456"
        assert deps.user_token == "xoxp-456"
        self.fake_client.chat_postEphemeral.assert_called_once()
        kwargs = self.fake_client.chat_postEphemeral.call_args.kwargs
        assert kwargs["user"] == "U456"
        assert kwargs["thread_ts"] == "1700000000.000100"
        assert "Runbook: Deploys" in kwargs["markdown_text"]
        self.fake_client.chat_postMessage.assert_not_called()

    @patch("runbooks.review.review_thread")
    def test_stays_quiet_when_nothing_changed(self, review_thread):
        review_thread.return_value = run_result(
            "slack_search_public_and_private", final_output="Nothing to add."
        )

        self.review()

        self.fake_client.chat_postEphemeral.assert_not_called()

    @patch("runbooks.review.review_thread")
    def test_logs_review_errors(self, review_thread, caplog):
        review_thread.side_effect = Exception("test exception")

        self.review()

        self.fake_client.chat_postEphemeral.assert_not_called()
        assert "test exception" in caplog.text
