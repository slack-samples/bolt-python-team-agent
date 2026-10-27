import json
from unittest.mock import Mock

from agent.guardrails import runbook_searches_only


def check(tool_name, **arguments):
    data = Mock()
    data.context.tool_name = tool_name
    data.context.tool_arguments = json.dumps(arguments)
    return runbook_searches_only.guardrail_function(data).behavior["type"]


def test_allows_runbook_searches_in_channels():
    assert (
        check(
            "slack_search_public_and_private",
            keywords=["Runbook"],
            content_types="files",
            channel_types="public_channel,private_channel",
        )
        == "allow"
    )


def test_rejects_searches_that_reach_dms():
    assert (
        check(
            "slack_search_public_and_private",
            keywords=["Runbook"],
            content_types="files",
            channel_types="public_channel,private_channel,mpim,im",
        )
        == "reject_content"
    )


def test_rejects_searches_without_channel_types():
    assert (
        check(
            "slack_search_public_and_private",
            keywords=["Runbook"],
            content_types="files",
        )
        == "reject_content"
    )


def test_rejects_message_searches():
    assert (
        check(
            "slack_search_public_and_private",
            keywords=["offer", "letter"],
            content_types="messages",
            channel_types="public_channel",
        )
        == "reject_content"
    )


def test_allows_other_tools():
    assert check("slack_read_canvas", canvas_id="F123") == "allow"
