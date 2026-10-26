from logging import Logger

from slack_bolt import Ack, BoltContext
from slack_sdk import WebClient

from agent import save_to_runbook
from listeners.views.runbook_suggestion_builder import (
    build_runbook_saving_blocks,
    build_runbook_suggestion_blocks,
)


def handle_add_to_runbook(
    ack: Ack, body: dict, client: WebClient, context: BoltContext, logger: Logger
):
    """Save a thread to a runbook as the person who clicked the button."""
    ack()

    channel_id = context.channel_id
    user_id = context.user_id
    message = body["message"]
    thread_ts = message.get("thread_ts", message["ts"])
    topic = body["actions"][0]["value"]

    if not context.user_token:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            thread_ts=thread_ts,
            text="Connect the Slack MCP Server from my Home tab first. I save runbooks as you, so your edits show your name.",
        )
        return

    try:
        client.chat_update(
            channel=channel_id,
            ts=message["ts"],
            text=f"{topic}: saving to a runbook",
            blocks=build_runbook_saving_blocks(topic, user_id),
        )
        permalink = client.chat_getPermalink(channel=channel_id, message_ts=thread_ts)
        update = save_to_runbook(
            channel_id=channel_id,
            thread_ts=thread_ts,
            permalink=permalink["permalink"],
            topic=topic,
            user_token=context.user_token,
        )
        if update.changed:
            client.chat_update(
                channel=channel_id,
                ts=message["ts"],
                markdown_text=update.note,
            )
            return
        client.chat_update(
            channel=channel_id,
            ts=message["ts"],
            text=f"This thread looks like it belongs in a runbook: {topic}",
            blocks=build_runbook_suggestion_blocks(topic),
        )
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            thread_ts=thread_ts,
            markdown_text=update.note,
        )
    except Exception as e:
        logger.exception("Failed to save thread to a runbook")
        client.chat_update(
            channel=channel_id,
            ts=message["ts"],
            text=f"This thread looks like it belongs in a runbook: {topic}",
            blocks=build_runbook_suggestion_blocks(topic),
        )
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            thread_ts=thread_ts,
            text=f":warning: Couldn't save this to a runbook. ({e})",
        )
