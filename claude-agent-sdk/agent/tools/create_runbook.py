from claude_agent_sdk import tool
from slack_sdk.errors import SlackApiError

from agent.context import agent_deps_var

CREATE_RUNBOOK_DESCRIPTION = """\
Create a runbook as a tab in the current channel so the whole team can read and edit it.

Only create a runbook when `list_runbooks` shows none that covers the topic.\
"""


@tool(
    name="create_runbook",
    description=CREATE_RUNBOOK_DESCRIPTION,
    input_schema={
        "type": "object",
        "properties": {
            "markdown": {
                "type": "string",
                "description": "The runbook as markdown, with short sections for when to use it, the steps, and who to ask.",
            },
            "topic": {
                "type": "string",
                "description": "What the runbook covers, such as `Rotating the signing secret`. It's titled `Runbook: <topic>`.",
            },
        },
        "required": ["markdown", "topic"],
    },
)
async def create_runbook_tool(args):
    """Create a runbook titled `Runbook: <topic>` as a channel tab."""
    deps = agent_deps_var.get()
    try:
        created = await deps.client.canvases_create(
            title=f"Runbook: {args['topic']}",
            document_content={
                "type": "markdown",
                "markdown": args["markdown"],
            },
            channel_id=deps.channel_id,
        )
        info = await deps.client.files_info(file=created["canvas_id"])
        file = info["file"]
        text = f"Created [{file['title']}]({file['permalink']})."
    except SlackApiError as e:
        detail = e.response.get("detail")
        if detail:
            text = (
                f"Could not create the runbook: {e.response['error']} ({detail}). "
                "Fix the markdown and call create_runbook again."
            )
        else:
            text = f"Could not create the runbook: {e.response['error']}"
    return {
        "content": [
            {
                "type": "text",
                "text": text,
            },
        ],
    }
