from logging import Logger

from slack_bolt.context.async_context import AsyncBoltContext
from slack_bolt.context.say.async_say import AsyncSay
from slack_bolt.context.say_stream.async_say_stream import AsyncSayStream
from slack_bolt.context.set_status.async_set_status import AsyncSetStatus
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from listeners.views.feedback_builder import build_feedback_blocks
from thread_context import session_store

LEARNED_SUBTYPES = {None, "file_share", "thread_broadcast"}

RUNBOOK_WRITES = {
    "mcp__agent-tools__create_runbook",
    "mcp__slack-mcp__slack_create_canvas",
    "mcp__slack-mcp__slack_update_canvas",
}


async def handle_message(
    client: AsyncWebClient,
    context: AsyncBoltContext,
    event: dict,
    logger: Logger,
    say: AsyncSay,
    say_stream: AsyncSayStream,
    set_status: AsyncSetStatus,
):
    """Handle messages sent to the agent via DM or in threads the bot is part of.

    The agent also learns from channel messages, adding anything they settle
    to the team's runbooks.
    """
    if event.get("bot_id"):
        return

    is_dm = event.get("channel_type") == "im"
    is_thread_reply = event.get("thread_ts") is not None

    if not is_dm and event.get("subtype") in LEARNED_SUBTYPES:
        try:
            deps = AgentDeps(
                client=client,
                user_id=context.user_id,
                channel_id=context.channel_id,
                thread_ts=event.get("thread_ts") or event["ts"],
                message_ts=event["ts"],
                user_token=context.user_token,
            )
            learned_text, _, tool_names = await run_agent(
                f"Learn from this channel message:\n\n{event.get('text', '')}",
                deps=deps,
            )
            if RUNBOOK_WRITES.intersection(tool_names):
                await client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.user_id,
                    thread_ts=event.get("thread_ts"),
                    markdown_text=learned_text,
                )
        except Exception:
            logger.exception("Failed to learn from message")

    # Skip message subtypes (edits, deletes, etc.).
    if event.get("subtype"):
        return

    if is_dm:
        pass
    elif is_thread_reply:
        # Channel thread replies are handled only if the bot is already engaged
        session = session_store.get_session(context.channel_id, event["thread_ts"])
        if session is None:
            return
    else:
        # Top-level channel messages are handled by app_mentioned
        return

    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event["ts"]

        # Get session ID for conversation context
        existing_session_id = session_store.get_session(channel_id, thread_ts)

        # Set assistant thread status with loading messages
        await set_status(
            status="Thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        # Run the agent with deps for tool access
        user_id = context.user_id
        deps = AgentDeps(
            client=client,
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=event["ts"],
            user_token=context.user_token,
        )
        response_text, new_session_id, _ = await run_agent(
            text, session_id=existing_session_id, deps=deps
        )

        # Stream response in thread with feedback buttons
        streamer = await say_stream()
        await streamer.append(markdown_text=response_text)
        feedback_blocks = build_feedback_blocks()
        await streamer.stop(blocks=feedback_blocks)

        # Store session ID for future context
        if new_session_id:
            session_store.set_session(channel_id, thread_ts, new_session_id)

    except Exception as e:
        logger.exception("Failed to handle message")
        await say(
            text=f":warning: Something went wrong! ({e})",
            thread_ts=event.get("thread_ts") or event.get("ts"),
        )
