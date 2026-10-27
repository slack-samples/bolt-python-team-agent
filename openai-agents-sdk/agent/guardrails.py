import json

from agents import (
    ToolGuardrailFunctionOutput,
    ToolInputGuardrailData,
    tool_input_guardrail,
)

RUNBOOK_CHANNEL_TYPES = {"private_channel", "public_channel"}


@tool_input_guardrail
def runbook_searches_only(data: ToolInputGuardrailData) -> ToolGuardrailFunctionOutput:
    """Let a thread review search only for runbook files in channels, never DMs."""
    if data.context.tool_name != "slack_search_public_and_private":
        return ToolGuardrailFunctionOutput.allow()
    arguments = json.loads(data.context.tool_arguments or "{}")
    channel_types = set(arguments.get("channel_types", "").split(","))
    keywords = [keyword.lower() for keyword in arguments.get("keywords", [])]
    if (
        arguments.get("content_types") == "files"
        and channel_types <= RUNBOOK_CHANNEL_TYPES
        and any("runbook" in keyword for keyword in keywords)
    ):
        return ToolGuardrailFunctionOutput.allow()
    return ToolGuardrailFunctionOutput.reject_content(
        "Search only for runbooks: use the keyword `Runbook`, set `content_types` "
        "to `files`, and set `channel_types` to `public_channel,private_channel`."
    )
