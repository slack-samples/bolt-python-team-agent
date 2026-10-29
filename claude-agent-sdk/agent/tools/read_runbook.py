from claude_agent_sdk import tool
from slack_sdk.errors import SlackApiError

from agent.context import agent_deps_var

READ_RUNBOOK_DESCRIPTION = """\
Read a runbook's content as markdown.

Read a runbook before you answer from it.\
"""


@tool(
    name="read_runbook",
    description=READ_RUNBOOK_DESCRIPTION,
    input_schema={
        "type": "object",
        "properties": {
            "canvas_id": {
                "type": "string",
                "description": "The runbook's canvas ID from `list_runbooks`, such as `F0123ABCD`.",
            },
        },
        "required": ["canvas_id"],
    },
)
async def read_runbook_tool(args):
    """Read a runbook's content as markdown."""
    deps = agent_deps_var.get()
    try:
        response = await deps.client.api_call(
            "canvases.getContent",
            params={
                "canvas_id": args["canvas_id"],
            },
        )
        text = response.get("content", "")
    except SlackApiError as e:
        text = f"Could not read the runbook: {e.response['error']}"
    return {
        "content": [
            {
                "type": "text",
                "text": text,
            },
        ],
    }
