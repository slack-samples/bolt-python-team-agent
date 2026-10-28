import logging
from unittest.mock import AsyncMock, Mock, patch

from slack_bolt import BoltContext
from slack_sdk import WebClient

from listeners.events.app_mentioned import handle_app_mentioned

test_logger = logging.getLogger(__name__)


@patch("listeners.events.app_mentioned.run_agent", new_callable=AsyncMock)
def test_mention_runs_the_agent_without_a_user_token(run_agent):
    context = Mock(BoltContext)
    context.channel_id = "C123"
    context.user_id = "U123"
    context.user_token = None
    run_agent.return_value = Mock(final_output="Here's the runbook.")
    say_stream = Mock()

    handle_app_mentioned(
        client=Mock(WebClient),
        context=context,
        event={
            "text": "<@B123> is there a runbook for deploys?",
            "ts": "1700000000.000100",
        },
        logger=test_logger,
        say=Mock(),
        say_stream=say_stream,
        set_status=Mock(),
    )

    agent_input, deps = run_agent.call_args.args
    assert agent_input == "is there a runbook for deploys?"
    assert deps.user_token is None
    say_stream.return_value.append.assert_called_once_with(
        markdown_text="Here's the runbook."
    )
