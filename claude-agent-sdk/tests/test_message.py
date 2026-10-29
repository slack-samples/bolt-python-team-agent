import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from listeners.events.message import handle_message

test_logger = logging.getLogger(__name__)

LEARNED = "Added the steps to [Runbook: Deploys](https://example.com)."


class TestMessage:
    def setup_method(self):
        self.fake_client = Mock(AsyncWebClient)
        self.fake_client.chat_postEphemeral = AsyncMock()
        self.fake_context = Mock(AsyncBoltContext)
        self.fake_context.channel_id = "C123"
        self.fake_context.user_id = "U123"
        self.fake_context.user_token = "xoxp-123"

    async def handle(self, event):
        await handle_message(
            client=self.fake_client,
            context=self.fake_context,
            event=event,
            logger=test_logger,
            say=AsyncMock(),
            say_stream=AsyncMock(),
            set_status=AsyncMock(),
        )

    @pytest.mark.asyncio
    @patch("listeners.events.message.run_agent", new_callable=AsyncMock)
    async def test_learns_from_a_channel_message_as_its_author(self, run_agent):
        run_agent.return_value = (
            LEARNED,
            None,
            ["mcp__slack-mcp__slack_update_canvas"],
        )

        await self.handle(
            {
                "channel_type": "channel",
                "text": "Fixed it: rotate the signing secret, then redeploy",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        learn_input = run_agent.call_args.args[0]
        deps = run_agent.call_args.kwargs["deps"]
        assert learn_input.startswith("Learn from this channel message")
        assert "rotate the signing secret" in learn_input
        assert deps.user_id == "U123"
        assert deps.user_token == "xoxp-123"
        kwargs = self.fake_client.chat_postEphemeral.call_args.kwargs
        assert kwargs["user"] == "U123"
        assert kwargs["thread_ts"] == "1700000000.000100"
        assert "Runbook: Deploys" in kwargs["markdown_text"]

    @pytest.mark.asyncio
    @patch("listeners.events.message.run_agent", new_callable=AsyncMock)
    async def test_stays_quiet_when_no_runbook_changed(self, run_agent):
        run_agent.return_value = (
            "Nothing to keep.",
            None,
            ["mcp__slack-mcp__slack_search_public_and_private"],
        )

        await self.handle(
            {
                "channel_type": "group",
                "text": "Lunch at noon?",
                "ts": "1700000000.000100",
            }
        )

        run_agent.assert_called_once()
        self.fake_client.chat_postEphemeral.assert_not_called()

    @pytest.mark.asyncio
    @patch("listeners.events.message.run_agent", new_callable=AsyncMock)
    async def test_learns_from_broadcast_thread_replies(self, run_agent):
        run_agent.return_value = ("Nothing to keep.", None, [])

        await self.handle(
            {
                "channel_type": "channel",
                "subtype": "thread_broadcast",
                "text": "Fixed: restarting the worker cleared the queue",
                "thread_ts": "1700000000.000100",
                "ts": "1700000000.000200",
            }
        )

        run_agent.assert_called_once()

    @pytest.mark.asyncio
    @patch("listeners.events.message.run_agent", new_callable=AsyncMock)
    async def test_logs_learning_errors(self, run_agent, caplog):
        run_agent.side_effect = Exception("test exception")

        await self.handle(
            {
                "channel_type": "channel",
                "text": "Fixed it: rotate the signing secret",
                "ts": "1700000000.000100",
            }
        )

        assert "test exception" in caplog.text

    @pytest.mark.asyncio
    @patch("listeners.events.message.run_agent", new_callable=AsyncMock)
    async def test_learns_with_the_bot_token_without_a_user_token(self, run_agent):
        self.fake_context.user_token = None
        run_agent.return_value = (
            LEARNED,
            None,
            ["mcp__agent-tools__create_runbook"],
        )

        await self.handle(
            {
                "channel_type": "channel",
                "text": "Fixed it: rotate the signing secret",
                "ts": "1700000000.000100",
            }
        )

        deps = run_agent.call_args.kwargs["deps"]
        assert deps.user_token is None
        self.fake_client.chat_postEphemeral.assert_called_once()

    @pytest.mark.asyncio
    @patch("listeners.events.message.run_agent", new_callable=AsyncMock)
    async def test_does_not_learn_from_edits_or_bots(self, run_agent):
        await self.handle(
            {
                "channel_type": "channel",
                "subtype": "message_changed",
                "ts": "1700000000.000100",
            }
        )
        await self.handle(
            {
                "bot_id": "B123",
                "channel_type": "channel",
                "text": "Added the steps to the runbook.",
                "ts": "1700000000.000200",
            }
        )

        run_agent.assert_not_called()
