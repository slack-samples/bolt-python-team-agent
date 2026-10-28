from agents import function_tool
from agents.run_context import RunContextWrapper
from slack_sdk.errors import SlackApiError

from agent.deps import AgentDeps


@function_tool
async def create_runbook(
    wrapper: RunContextWrapper[AgentDeps], topic: str, markdown: str
) -> str:
    """Create a runbook as a tab in the current channel so the whole team can read and edit it.

    Only create a runbook when `list_runbooks` shows none that covers the topic.

    Args:
        topic: What the runbook covers, such as `Rotating the signing secret`. It's titled `Runbook: <topic>`.
        markdown: The runbook as markdown, with short sections for when to use it, the steps, and who to ask.
    """
    deps = wrapper.context
    try:
        created = deps.client.canvases_create(
            title=f"Runbook: {topic}",
            document_content={"type": "markdown", "markdown": markdown},
            channel_id=deps.channel_id,
        )
        file = deps.client.files_info(file=created["canvas_id"])["file"]
    except SlackApiError as e:
        detail = e.response.get("detail")
        if detail:
            return (
                f"Could not create the runbook: {e.response['error']} ({detail}). "
                "Fix the markdown and call create_runbook again."
            )
        return f"Could not create the runbook: {e.response['error']}"
    return f"Created [{file['title']}]({file['permalink']})."
