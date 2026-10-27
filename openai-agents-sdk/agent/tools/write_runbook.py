from agents import function_tool
from agents.run_context import RunContextWrapper
from slack_sdk.errors import SlackApiError

from agent.deps import AgentDeps


@function_tool
async def write_runbook(
    wrapper: RunContextWrapper[AgentDeps],
    topic: str,
    markdown: str,
    canvas_id: str | None = None,
) -> str:
    """Write a runbook, replacing its content or creating it.

    Send the whole runbook as markdown each time, keeping everything that's
    still true. A new runbook is added as a tab in the current channel so the
    whole team can read and edit it.

    Args:
        topic: What the runbook covers, such as `Rotating the signing secret`. It's titled `Runbook: <topic>`.
        markdown: The full runbook as markdown, with short sections for when to use it, the steps, and who to ask.
        canvas_id: The canvas ID of the runbook to replace, from `list_runbooks`. Leave it empty to create a new runbook.
    """
    deps = wrapper.context
    document_content = {"type": "markdown", "markdown": markdown}
    try:
        if canvas_id:
            deps.client.canvases_edit(
                canvas_id=canvas_id,
                changes=[
                    {"operation": "replace", "document_content": document_content}
                ],
            )
        else:
            created = deps.client.canvases_create(
                title=f"Runbook: {topic}",
                document_content=document_content,
                channel_id=deps.channel_id,
            )
            canvas_id = created["canvas_id"]
        file = deps.client.files_info(file=canvas_id)["file"]
        return f"Wrote [{file['title']}]({file['permalink']})."
    except SlackApiError as e:
        detail = e.response.get("detail")
        if detail:
            return (
                f"Could not write the runbook: {e.response['error']} ({detail}). "
                "Fix the markdown and call write_runbook again."
            )
        return f"Could not write the runbook: {e.response['error']}"
