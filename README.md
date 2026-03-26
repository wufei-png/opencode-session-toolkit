# opencode-session-toolkit

`opencode-session-toolkit` is a skill for reading the local OpenCode SQLite database, querying sessions across directories, inspecting messages and schema details, and exporting matched sessions to Markdown files.

## One-Line Install

```bash
# English (default)
curl -fsSL https://raw.githubusercontent.com/wufei-png/opencode-session-toolkit/main/install.sh | bash

# 中文版本
LANG_CHOICE=2 bash -c "$(curl -fsSL https://raw.githubusercontent.com/wufei-png/opencode-session-toolkit/main/install.sh)"
```

This will:
- Download all skill files to `~/.agents/skills/opencode-session-toolkit/`
- Create symlinks in `~/.claude/skills/` and `~/.cursor/skills/`

## What this skill does

- Resolve the local OpenCode database path with `opencode db path`
- Run read-only SQLite queries against `session`, `message`, `part`, and `project`
- Inspect session/message JSON content for debugging and analysis
- Export matched sessions into one-Markdown-per-session archives with the bundled script

## Repository layout

- `SKILL.md`: English skill instructions
- `scripts/export_opencode_sessions.py`: Markdown export utility
- `references/schema.md`: schema and index notes
- `cn-version/opencode-session-toolkit-cn`: Chinese version of this skill

## Chinese version

The Chinese version lives in [`cn-version/opencode-session-toolkit-cn`](./opencode-session-toolkit-cn).

## ClawHub

- ClawHub: https://clawhub.ai/wufei-png/opencode-session-toolkit

## Typical use cases

- List recent OpenCode sessions across projects
- Filter sessions by directory, project, title, or time range
- Read a single session's message payloads as JSON
- Export selected sessions into Markdown archives for later review
