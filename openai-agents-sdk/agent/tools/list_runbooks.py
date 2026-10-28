from agents import function_tool
from agents.run_context import RunContextWrapper
from slack_sdk.errors import SlackApiError

from agent.deps import AgentDeps

RUNBOOK_PREFIX = "Runbook:"


@function_tool
async def list_runbooks(wrapper: RunContextWrapper[AgentDeps]) -> str:
    """List the team's runbooks: canvases titled `Runbook: <topic>`.

    Call this before answering a request or writing a runbook, then read the
    one that covers the topic with `read_runbook`.
    """
    deps = wrapper.context
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
