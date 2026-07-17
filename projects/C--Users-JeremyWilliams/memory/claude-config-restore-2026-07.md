---
name: claude-config-restore-2026-07
description: Canonical Claude Code config repo + the leaked keys still awaiting rotation after the July 2026 machine reset
metadata: 
  node_type: memory
  type: project
  originSessionId: 2856380f-2b23-4f30-8816-6fcba2b48106
---

After the 2026-07-13 Windows reset, `~/.claude` was restored and consolidated. The canonical source of truth is **`Dobeu-tech-eco/dobeutech-claude-code-custom`** (branch `consolidate/windows-v2`, PR #3) — install it with `npm i -g @jwdobeutechsolutions/dobeutech-claude-code-custom`. The other config repos (`fk-everything-claude-code`, `claudeconfig`, `claudecode-config`, `dobeu-claude-skills`) are noise or forks; do not restore from them.

**Open action as of 2026-07-13 — four live API keys are still un-rotated**, committed in git history in `dobeutech/claudecode-config` (private): a GitHub PAT, OpenAI key, Notion token, and Tavily key, plus a `.credentials.json`. Deleting the file does not help — they are in history, so the repo must be deleted. The same `.env-mcp` also sits in a git repo on `G:\My Drive` (that copy appears never to have been pushed). Full checklist with rotation URLs is at `~/.claude/SECURITY_REMEDIATION.md`.

The GitHub PAT is exposed on a *second* independent path too: the 24-credential Doppler vault leak documented in `dobeu-composio-automate`, which was marked "RISK-ACCEPTED — rotation declined" in April 2026. That decision was made without knowing about the git-history exposure, so it is worth revisiting.

Also unresolved: 23 `@inline` plugins were in use pre-reset and are gone. Only `datadog` is recoverable from the official marketplace; only 4 (`beads`, `holocron`, `subtask`, `wit`) were ever actually invoked. See `~/.claude/PLUGIN_RECOVERY.md`.

**Update 2026-07-17 (config audit):** A *fifth*, separate secret surfaced — the Composio MCP `X-API-Key` (`ck_wNN…`) sat in plaintext in the home-level `.claude.json`. Now remediated: user revoked it at Composio; the header was swapped to `${COMPOSIO_API_KEY}` (set the env var with the new key via `[Environment]::SetEnvironmentVariable(...,'User')`, then restart). The stale `~/.claude/backups/` snapshot (only other on-disk copy of the dead key + OAuth PII) was deleted. **The four git-history keys above (GitHub PAT, OpenAI, Notion, Tavily) + `.credentials.json` are still OPEN.** Backup split clarified: `Dobeu-tech-eco/dobeutech-claude-code-custom` is the **public** npm distributable; the new **private** `Dobeu-tech-eco/claude-code-config-backup` holds the raw machine `~/.claude` backup (secrets gitignored via whitelist). Audit also disabled 56 zero-use plugins (131→75 enabled), archived dup agents/skills to `_archive/`, dropped overlapping PowerShell hooks, and added a daily Windows scheduled-task auto-commit. See [[wsl-claude-config-mirror]].
