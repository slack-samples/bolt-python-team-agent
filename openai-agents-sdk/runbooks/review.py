from logging import Logger

from agents import RunResult, ToolCallItem
from slack_sdk import WebClient

from agent import AgentDeps, run_review

RUNBOOK_WRITES = {"slack_create_canvas", "slack_update_canvas"}


def build_review_input(messages: list[dict], permalink: str) -> str:
    """Write out a thread with who said what, ending with the new message."""
    lines = [
        "A new message was posted. If it settles something a runbook should hold, add it.",
        "Earlier messages in the thread are context.",
        f"Link: {permalink}",
        "",
    ]
    for message in messages:
        author = "agent" if message.get("bot_id") else f"<@{message.get('user')}>"
        lines.append(f"{author}: {message.get('text', '')}")
    return "\n".join(lines)


def changed_a_runbook(result: RunResult) -> bool:
    """Check whether a run created or updated a canvas."""
    return any(
        isinstance(item, ToolCallItem)
        and getattr(item.raw_item, "name", None) in RUNBOOK_WRITES
        for item in result.new_items
    )


def review_message(
    client: WebClient,
    channel_id: str,
    event: dict,
    user_id: str,
    user_token: str,
    logger: Logger,
) -> None:
    """Add what a channel message settled to a runbook, acting as its author."""
    try:
        thread_ts = event.get("thread_ts") or event["ts"]
        replies = client.conversations_replies(
            channel=channel_id, ts=thread_ts, latest=event["ts"], inclusive=True
        )
        permalink = client.chat_getPermalink(channel=channel_id, message_ts=event["ts"])
        deps = AgentDeps(
            client=client,
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=event["ts"],
            user_token=user_token,
        )
        result = run_review(
            build_review_input(replies["messages"], permalink["permalink"]), deps
        )
        if changed_a_runbook(result):
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                thread_ts=event.get("thread_ts"),
                markdown_text=result.final_output,
            )
    except Exception:
        logger.exception("Failed to review message for runbook updates")
