# AGENTS.md

This file provides guidance to coding agents when working with code in this repository.

## What This Is

A **Team Agent** for Slack built with Bolt for Python and the **OpenAI Agents SDK**. It keeps a team's runbooks current and helps route requests. Runbooks are Slack canvases titled `Runbook: <topic>` that the agent reads and writes through the Slack MCP Server. When a channel thread goes quiet (`runbooks/`), a tool-less check (`agent/runbook_check.py`) decides whether it's worth saving and the bot offers an _Add to runbook_ button. Clicking it runs `agent/runbook_agent.py` with the clicker's token and a restricted set of Slack MCP tools. It includes one app tool (emoji reactions).

## Slack Plugin

To install the Slack plugin for your coding agent, follow [Claude Code, Codex, Cursor, and Other Coding Agents](./README.md#claude-code-codex-cursor-and-other-coding-agents) in the README.

## Before you finish

Run `ruff check .`, `ruff format --check .`, and `pytest`. CI runs the same on every PR.

## Code Style

- Snake-case filenames
- No code comments. Make the code explain itself with clear names, tests, or types. Put the reason for a change in the PR description.
