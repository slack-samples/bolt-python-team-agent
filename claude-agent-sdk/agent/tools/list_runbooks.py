from claude_agent_sdk import tool
from slack_sdk.errors import SlackApiError

from agent.context import agent_deps_var

RUNBOOK_PREFIX = "Runbook:"

LIST_RUNBOOKS_DESCRIPTION = """\
List the team's runbooks: canvases titled `Runbook: <topic>`.

Call this before answering a request or writing a runbook, then read the \
one that covers the topic with `read_runbook`.\
"""


@tool(
    name="list_runbooks",
    description=LIST_RUNBOOKS_DESCRIPTION,
    input_schema={
        "type": "object",
        "properties": {},
    },
)
async def list_runbooks_tool(args):
    """List the canvases titled `Runbook: <topic>`."""
    deps = agent_deps_var.get()
    try:
        response = await deps.client.files_list(types="canvas")
        runbooks = [
            f"- [{file['title']}]({file['permalink']}) (`{file['id']}`)"
            for file in response.get("files", [])
            if file.get("title", "").startswith(RUNBOOK_PREFIX)
        ]
        text = "\n".join(runbooks) if runbooks else "No runbooks yet."
    except SlackApiError as e:
        text = f"Could not list runbooks: {e.response['error']}"
    return {
        "content": [
            {
                "type": "text",
                "text": text,
            },
        ],
    }
