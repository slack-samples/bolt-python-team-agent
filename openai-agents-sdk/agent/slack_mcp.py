from agents.mcp import MCPServerStreamableHttp, create_static_tool_filter

SLACK_MCP_URL = "https://mcp.slack.com/mcp"


def slack_mcp_server(
    user_token: str, allowed_tool_names: list[str] | None = None
) -> MCPServerStreamableHttp:
    """Connect to the Slack MCP Server as the user who owns the token."""
    return MCPServerStreamableHttp(
        params={
            "url": SLACK_MCP_URL,
            "headers": {"Authorization": f"Bearer {user_token}"},
        },
        tool_filter=create_static_tool_filter(allowed_tool_names=allowed_tool_names),
    )
