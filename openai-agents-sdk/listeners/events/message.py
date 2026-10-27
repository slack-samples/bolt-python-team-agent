import asyncio
from logging import Logger

from slack_bolt import BoltContext, Say, SayStream, SetStatus
from slack_sdk import WebClient

from agent import AgentDeps, run_agent
from listeners.views.feedback_builder import build_feedback_blocks
from thread_context import conversation_store

LEARNED_SUBTYPES = {None, "file_share", "thread_broadcast"}

RUNBOOK_WRITES = {"slack_create_canvas", "slack_update_canvas", "write_runbook"}


def handle_message(
    client: WebClient,
    context: BoltContext,
    event: dict,
    logger: Logger,
    say: Say,
    say_stream: SayStream,
    set_status: SetStatus,
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
            result = asyncio.run(
                run_agent(
                    f"Learn from this channel message:\n\n{event.get('text', '')}", deps
                )
            )
            if any(
                getattr(item.raw_item, "name", None) in RUNBOOK_WRITES
                for item in result.new_items
            ):
                client.chat_postEphemeral(
                    channel=context.channel_id,
                    user=context.user_id,
                    thread_ts=event.get("thread_ts"),
                    markdown_text=result.final_output,
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
        history = conversation_store.get_history(context.channel_id, event["thread_ts"])
        if history is None:
            return
    else:
        # Top-level channel messages are handled by app_mentioned
        return

    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event["ts"]

        user_id = context.user_id

        # Get conversation history
        history = conversation_store.get_history(channel_id, thread_ts)

        # Set assistant thread status with loading messages
        set_status(
            status="Thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        # Build input for the agent
        if history:
            input_items = history + [{"role": "user", "content": text}]
        else:
            input_items = text

        # Run the agent
        deps = AgentDeps(
            client=client,
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=event["ts"],
            user_token=context.user_token,
        )
        result = asyncio.run(run_agent(input_items, deps))

        # Stream response in thread with feedback buttons
        streamer = say_stream()
        streamer.append(markdown_text=result.final_output)
        feedback_blocks = build_feedback_blocks()
        streamer.stop(blocks=feedback_blocks)

        # Store conversation history
        conversation_store.set_history(channel_id, thread_ts, result.to_input_list())

    except Exception as e:
        logger.exception("Failed to handle message")
        say(
            text=f":warning: Something went wrong! ({e})",
            thread_ts=event.get("thread_ts") or event.get("ts"),
        )
