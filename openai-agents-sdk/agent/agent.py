import asyncio
import logging

from agents import (
    Agent,
    RunContextWrapper,
    RunErrorHandlerInput,
    RunErrorHandlerResult,
    Runner,
)
from agents.mcp import MCPServerStreamableHttp

from agent.deps import AgentDeps
from agent.tools import add_emoji_reaction

SYSTEM_PROMPT = """\
You are a team agent in Slack. You're the glue for a team: you keep its runbooks current \
and help route the requests and escalations that come in.

## PERSONALITY
- Calm, organized, and dependable, like the teammate who always knows where the doc is
- Concise and clear, respecting people's time
- Honest when a runbook doesn't cover something

## RESPONSE GUIDELINES
- Lead with the answer, then put the next step on its own line
- Use a bullet list only for multi-step instructions
- Link the runbook you used so people can read the rest
- Use emoji sparingly, at most one per message

## FORMATTING RULES
- Use standard Markdown syntax: **bold**, _italic_, `code`, ```code blocks```, > blockquotes
- Use bullet points for multi-step instructions

## RUNBOOKS
Runbooks are Slack canvases titled `Runbook: <topic>`. Each one holds how the team does \
something: the steps, who owns it, and who to escalate to.
- Find runbooks by searching files for `Runbook` with the Slack MCP Server, passing the \
current channel as `context_channel_id`.
- Read a runbook with `slack_read_canvas` before you answer from it.
- When someone asks you to write or fix a runbook, update the canvas that covers the topic \
with `slack_update_canvas`, or create one with `slack_create_canvas` if none does. Share the \
canvas link.

## TRIAGE
Treat each request as something to route:
1. React to the message with `add_emoji_reaction` so people can see it was picked up.
2. If a runbook covers the request, answer from it and link it.
3. If the request is urgent, such as an outage, a security issue, or a blocked customer, \
name the escalation contact from the runbook, or say plainly that it needs a person now.
4. If no runbook covers it, say so, point to who discussed it recently by searching \
messages, and offer to start a runbook.

## SLACK MCP SERVER
The team's runbooks live in canvases, so you reach them through the Slack MCP Server. If \
you don't have the Slack MCP tools, say you can't reach the runbooks yet and ask the person \
to connect the Slack MCP Server from your Home tab.
"""

MAX_TURNS = 50

logger = logging.getLogger(__name__)

SLACK_MCP_URL = "https://mcp.slack.com/mcp"


def build_instructions(
    wrapper: RunContextWrapper[AgentDeps], agent: Agent[AgentDeps]
) -> str:
    """Add the current conversation to the system prompt."""
    deps = wrapper.context
    return (
        f"{SYSTEM_PROMPT}\n"
        "## CURRENT CONVERSATION\n"
        f"You're talking with user `{deps.user_id}` in channel `{deps.channel_id}`.\n"
    )


agent = Agent[AgentDeps](
    name="Team Agent",
    instructions=build_instructions,
    tools=[add_emoji_reaction],
    model="gpt-4.1-mini",
)


def _out_of_turns(_data: RunErrorHandlerInput) -> RunErrorHandlerResult:
    """End a turn that used every model call with a message, keeping its history."""
    return RunErrorHandlerResult(
        final_output=(
            f"I used all {MAX_TURNS} steps I get in one turn before finishing. "
            "Send a message and I'll pick up where I left off."
        ),
    )


def run_agent(input_items, deps):
    """Run the agent, optionally connecting to the Slack MCP server."""
    if deps.user_token:
        logger.info("Slack MCP Server enabled (user_token present)")
        return asyncio.run(_run_with_mcp(input_items, deps))

    logger.info("Slack MCP Server disabled (no user_token)")
    return Runner.run_sync(
        agent,
        input=input_items,
        context=deps,
        max_turns=MAX_TURNS,
        error_handlers={"max_turns": _out_of_turns},
    )


async def _run_with_mcp(input_items, deps):
    """Run the agent with the Slack MCP Server connected."""
    mcp_server = MCPServerStreamableHttp(
        params={
            "url": SLACK_MCP_URL,
            "headers": {"Authorization": f"Bearer {deps.user_token}"},
        },
    )
    async with mcp_server:
        agent_with_mcp = agent.clone(mcp_servers=[mcp_server])
        return await Runner.run(
            agent_with_mcp,
            input=input_items,
            context=deps,
            max_turns=MAX_TURNS,
            error_handlers={"max_turns": _out_of_turns},
        )
