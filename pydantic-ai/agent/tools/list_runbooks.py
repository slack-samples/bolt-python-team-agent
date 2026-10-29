from pydantic_ai import RunContext
from slack_sdk.errors import SlackApiError

from agent.deps import AgentDeps

RUNBOOK_PREFIX = "Runbook:"


async def list_runbooks(ctx: RunContext[AgentDeps]) -> str:
    """List the team's runbooks: canvases titled `Runbook: <topic>`.

    Call this before answering a request or writing a runbook, then read the
    one that covers the topic with `read_runbook`.

    Args:
        ctx: The run context with dependencies.
    """
    deps = ctx.deps
    try:
        response = deps.client.files_list(types="canvas")
    except SlackApiError as e:
        return f"Could not list runbooks: {e.response['error']}"

    runbooks = [
        f"- [{file['title']}]({file['permalink']}) (`{file['id']}`)"
        for file in response.get("files", [])
        if file.get("title", "").startswith(RUNBOOK_PREFIX)
    ]
    if not runbooks:
        return "No runbooks yet."
    return "\n".join(runbooks)
