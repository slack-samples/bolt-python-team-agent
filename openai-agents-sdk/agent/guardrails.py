import json

from agents import (
    ToolGuardrailFunctionOutput,
    ToolInputGuardrailData,
    tool_input_guardrail,
)


@tool_input_guardrail
def runbook_searches_only(data: ToolInputGuardrailData) -> ToolGuardrailFunctionOutput:
    """Let the agent search for runbook files and nothing else."""
    if data.context.tool_name != "slack_search_public_and_private":
        return ToolGuardrailFunctionOutput.allow()
    arguments = json.loads(data.context.tool_arguments)
    if arguments.get("content_types") == "files" and "Runbook" in arguments.get(
        "keywords", []
    ):
        return ToolGuardrailFunctionOutput.allow()
    return ToolGuardrailFunctionOutput.reject_content(
        "Search only files with the keyword `Runbook`."
    )
