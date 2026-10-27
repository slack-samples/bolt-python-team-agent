import os
from logging import Logger

from agents import RunResult, ToolCallItem
from slack_sdk import WebClient

from agent import AgentDeps, review_thread

from .watch import ThreadWatch

DEFAULT_SETTLE_SECONDS = 300

RUNBOOK_WRITES = {"slack_create_canvas", "slack_update_canvas"}

thread_watch = ThreadWatch()


def review_when_settled(
    client: WebClient,
    channel_id: str,
    thread_ts: str,
    user_id: str,
    user_token: str | None,
    logger: Logger,
) -> None:
    """Add what a thread settled to the runbooks once it has been quiet for a while."""
    thread_watch.observe(
        channel_id,
        thread_ts,
        delay=float(os.environ.get("RUNBOOK_SETTLE_SECONDS", DEFAULT_SETTLE_SECONDS)),
        user_id=user_id,
        user_token=user_token,
        on_settled=lambda settled_user_id, settled_user_token: review_settled_thread(
            client, channel_id, thread_ts, settled_user_id, settled_user_token, logger
        ),
    )


def build_review_input(messages: list[dict], permalink: str) -> str:
    """Write out a quiet thread with who said what."""
    lines = [
        "This thread just went quiet. Add anything it settled to the team's runbooks.",
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


def review_settled_thread(
    client: WebClient,
    channel_id: str,
    thread_ts: str,
    user_id: str,
    user_token: str,
    logger: Logger,
) -> None:
    """Write what a quiet thread settled to a runbook and tell the person it ran as."""
    try:
        replies = client.conversations_replies(channel=channel_id, ts=thread_ts)
        permalink = client.chat_getPermalink(channel=channel_id, message_ts=thread_ts)
        deps = AgentDeps(
            client=client,
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=thread_ts,
            user_token=user_token,
        )
        result = review_thread(
            build_review_input(replies["messages"], permalink["permalink"]), deps
        )
        if changed_a_runbook(result):
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                thread_ts=thread_ts,
                markdown_text=result.final_output,
            )
    except Exception:
        logger.exception("Failed to review thread for runbook updates")
