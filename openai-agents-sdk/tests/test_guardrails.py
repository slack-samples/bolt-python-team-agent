import json
from unittest.mock import Mock

from agent.guardrails import runbook_searches_only


def check(tool_name, **arguments):
    data = Mock()
    data.context.tool_name = tool_name
    data.context.tool_arguments = json.dumps(arguments)
    return runbook_searches_only.guardrail_function(data).behavior["type"]


def test_allows_runbook_file_searches():
    assert (
        check(
            "slack_search_public_and_private",
            keywords=["Runbook"],
            content_types="files",
        )
        == "allow"
    )


def test_rejects_message_searches():
    assert (
        check(
            "slack_search_public_and_private",
            keywords=["Runbook"],
            content_types="messages",
        )
        == "reject_content"
    )


def test_rejects_other_file_searches():
    assert (
        check(
            "slack_search_public_and_private",
            keywords=["offer", "letter"],
            content_types="files",
        )
        == "reject_content"
    )


def test_allows_other_tools():
    assert check("slack_read_canvas", canvas_id="F123") == "allow"
