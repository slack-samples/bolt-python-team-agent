import logging
from unittest.mock import AsyncMock, Mock, patch

from slack_bolt import BoltContext
from slack_sdk import WebClient

from listeners.events.app_mentioned import handle_app_mentioned

test_logger = logging.getLogger(__name__)


@patch("listeners.events.app_mentioned.run_agent", new_callable=AsyncMock)
def test_mention_without_user_token_asks_to_connect(run_agent):
    context = Mock(BoltContext)
    context.channel_id = "C123"
    context.user_id = "U123"
    context.user_token = None
    say = Mock()

    handle_app_mentioned(
        client=Mock(WebClient),
        context=context,
        event={
            "text": "<@B123> is there a runbook for deploys?",
            "ts": "1700000000.000100",
        },
        logger=test_logger,
        say=say,
        say_stream=Mock(),
        set_status=Mock(),
    )

    run_agent.assert_not_called()
    assert "Connect the Slack MCP Server" in say.call_args.kwargs["text"]
