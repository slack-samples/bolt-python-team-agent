from agents import function_tool
from agents.run_context import RunContextWrapper
from slack_sdk.errors import SlackApiError

from agent.deps import AgentDeps


@function_tool
async def read_runbook(wrapper: RunContextWrapper[AgentDeps], canvas_id: str) -> str:
    """Read a runbook's content as markdown.

    Read a runbook before you answer from it, and before you rewrite it with
    `write_runbook`.

    Args:
        canvas_id: The runbook's canvas ID from `list_runbooks`, such as `F0123ABCD`.
    """
    deps = wrapper.context
    try:
        response = deps.client.api_call(
            "canvases.getContent", params={"canvas_id": canvas_id}
        )
    except SlackApiError as e:
        return f"Could not read the runbook: {e.response['error']}"
    return response.get("content", "")
