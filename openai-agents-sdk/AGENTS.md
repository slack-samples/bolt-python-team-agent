# AGENTS.md

This file provides guidance to coding agents when working with code in this repository.

## What This Is

A **Team Agent** for Slack built with Bolt for Python and the **OpenAI Agents SDK**. It keeps a team's runbooks current and helps route requests. Runbooks are Slack canvases titled `Runbook: <topic>` that the agent reads and writes through the Slack MCP Server. The same agent learns from each channel message by a connected user (`listeners/events/message.py`), adding anything it settles to a runbook as the author. It only gets the Slack MCP tools for runbooks. It includes one app tool (emoji reactions).

## Slack Plugin

To install the Slack plugin for your coding agent, follow [Claude Code, Codex, Cursor, and Other Coding Agents](./README.md#claude-code-codex-cursor-and-other-coding-agents) in the README.

## Before you finish

Run `ruff check .`, `ruff format --check .`, and `pytest`. CI runs the same on every PR.

## Code Style

- Snake-case filenames
- No code comments. Make the code explain itself with clear names, tests, or types. Put the reason for a change in the PR description.
