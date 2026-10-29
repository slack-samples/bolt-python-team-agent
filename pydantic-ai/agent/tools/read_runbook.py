from pydantic_ai import RunContext
from slack_sdk.errors import SlackApiError

from agent.deps import AgentDeps


async def read_runbook(ctx: RunContext[AgentDeps], canvas_id: str) -> str:
    """Read a runbook's content as markdown.

    Read a runbook before you answer from it.

    Args:
        ctx: The run context with dependencies.
        canvas_id: The runbook's canvas ID from `list_runbooks`, such as `F0123ABCD`.
    """
    deps = ctx.deps
    try:
        response = deps.client.api_call(
            "canvases.getContent",
            params={
                "canvas_id": canvas_id,
            },
        )
    except SlackApiError as e:
        return f"Could not read the runbook: {e.response['error']}"
    return response.get("content", "")
