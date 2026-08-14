# AI Stack Config Sync

Canonical configuration sync hub for Claude Desktop, Claude Code CLI, Codex CLI + Codex/ChatGPT Beta desktop, Cursor, and Cursor CLI.

## Layout

- `.agent/` — checkpoint state (`progress.md`, `tasks.json`, `state.json`)
- `canonical/` — source of truth for MCP, instructions, rules, hooks, plugins, skills
- `emitters/` — idempotent per-tool writers
- `verify/` — SHA256 drift checks and remediation helpers
- `backups/` — local timestamped config-only backups (ignored by git except `.gitkeep`)
- `reports/` — audits, synthesis, diagrams, handoff notes
- `plugins/stack-sync/` — local plugin packaging the drift checker

## Safety rules

1. Never copy auth tokens, API keys, or credential files into this hub.
2. Prefer env-var references (`${env:NAME}`) over inline secrets.
3. Apply one tool at a time with automatic rollback from CP0 backups.
4. Touch `~/.claude.json` only through the `claude mcp` CLI.

## Quick commands

```powershell
pwsh -NoProfile -File .\verify\drift-check.ps1
pwsh -NoProfile -File .\emitters\apply-all.ps1 -DryRun
pwsh -NoProfile -File .\verify\cp0-backup.ps1
```
