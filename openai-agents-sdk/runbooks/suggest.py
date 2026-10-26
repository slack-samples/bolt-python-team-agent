import os
from logging import Logger

from slack_sdk import WebClient

from agent import check_thread
from listeners.views.runbook_suggestion_builder import build_runbook_suggestion_blocks

from .watch import ThreadWatch

DEFAULT_SETTLE_SECONDS = 300

thread_watch = ThreadWatch()


def suggest_when_settled(
    client: WebClient, channel_id: str, thread_ts: str, logger: Logger
) -> None:
    """Check a thread for runbook material once it has been quiet for a while."""
    thread_watch.observe(
        channel_id,
        thread_ts,
        delay=float(os.environ.get("RUNBOOK_SETTLE_SECONDS", DEFAULT_SETTLE_SECONDS)),
        on_settled=lambda: suggest_runbook(client, channel_id, thread_ts, logger),
    )


def build_transcript(messages: list[dict]) -> str:
    """Write out a thread with who said what."""
    lines = []
    for message in messages:
        author = "agent" if message.get("bot_id") else f"<@{message.get('user')}>"
        lines.append(f"{author}: {message.get('text', '')}")
    return "\n".join(lines)


def suggest_runbook(
    client: WebClient, channel_id: str, thread_ts: str, logger: Logger
) -> None:
    """Offer to save a quiet thread to a runbook when it settled something."""
    try:
        replies = client.conversations_replies(channel=channel_id, ts=thread_ts)
        check = check_thread(build_transcript(replies["messages"]))
        if not check.worth_saving or not check.topic:
            return
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"This thread looks like it belongs in a runbook: {check.topic}",
            blocks=build_runbook_suggestion_blocks(check.topic),
        )
    except Exception:
        logger.exception("Failed to check thread for runbook material")
