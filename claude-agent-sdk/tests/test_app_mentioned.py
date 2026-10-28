import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from listeners.events.app_mentioned import handle_app_mentioned

test_logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@patch("listeners.events.app_mentioned.run_agent", new_callable=AsyncMock)
async def test_mention_runs_the_agent_without_a_user_token(run_agent):
    context = Mock(AsyncBoltContext)
    context.channel_id = "C123"
    context.user_id = "U123"
    context.user_token = None
    run_agent.return_value = ("Here's the runbook.", None, [])
    streamer = Mock()
    streamer.append = AsyncMock()
    streamer.stop = AsyncMock()

    await handle_app_mentioned(
        client=Mock(AsyncWebClient),
        context=context,
        event={
            "text": "<@B123> is there a runbook for deploys?",
            "ts": "1700000000.000100",
        },
        logger=test_logger,
        say=AsyncMock(),
        say_stream=AsyncMock(return_value=streamer),
        set_status=AsyncMock(),
    )

    agent_input = run_agent.call_args.args[0]
    deps = run_agent.call_args.kwargs["deps"]
    assert agent_input == "is there a runbook for deploys?"
    assert deps.user_token is None
    streamer.append.assert_called_once_with(markdown_text="Here's the runbook.")
