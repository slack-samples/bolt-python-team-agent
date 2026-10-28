# AGENTS.md

This file provides guidance to coding agents when working with code in this repository.

## What This Is

A **Team Agent** for Slack built with Bolt for Python and the **OpenAI Agents SDK**. It keeps a team's runbooks current and helps route requests. Runbooks are Slack canvases titled `Runbook: <topic>`. With the bot token, the agent lists, reads, and creates them with tools in `agent/tools/` (`files.list`, `canvases.getContent`, `canvases.create`). When the person has connected the Slack MCP Server, it uses the MCP runbook tools instead, which can also edit runbooks. The same agent learns from each channel message (`listeners/events/message.py`), adding anything it settles to a runbook. It also includes one app tool (emoji reactions).

## Slack Plugin

To install the Slack plugin for your coding agent, follow [Claude Code, Codex, Cursor, and Other Coding Agents](./README.md#claude-code-codex-cursor-and-other-coding-agents) in the README.

## Before you finish

Run `ruff check .`, `ruff format --check .`, and `pytest`. CI runs the same on every PR.

## Code Style

- Snake-case filenames
- No code comments. Make the code explain itself with clear names, tests, or types. Put the reason for a change in the PR description.
