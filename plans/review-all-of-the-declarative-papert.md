# Restore & Consolidate Claude Code Config (Windows 11)

## Context

Jeremy reset his Windows 11 machine on 2026-07-13 and lost his Claude Code configuration. A partial restore already ran from a Google Drive backup (agents + skills), but `commands/`, `hooks/`, `rules/`, and the statusline are all still empty. His real config is scattered across six GitHub repos and a stale Drive backup, with no single source of truth.

Goal: get the local machine to full parity with the best of everything he has saved, then consolidate it into one canonical, Windows-correct, reproducible repo so the next reset is a one-command restore.

**Critical constraint discovered during exploration:** the hooks in his repo are Linux-only (bash + `jq` + `tmux`) *and* use an invalid matcher syntax that would never fire in real Claude Code. They cannot be copied — they must be rewritten. One of them unconditionally `exit 1`s on `npm run dev`, which would brick dev-server startup on this machine.

---

## What is already good — DO NOT CLOBBER

The live `~/.claude` (2026-07-13) is the newest state of all sources. It has things no backup contains:

- `settings.json` — Composio plugin + marketplace registration
- `plugins/installed_plugins.json` + `known_marketplaces.json` — composio@composio v0.2.1, 2 marketplaces
- `~/.claude.json` — Max 20x OAuth, 3 stdio MCP servers, 22 connected claude.ai connectors
- `agents/` — 17 agents (byte-identical to Drive)
- `skills/` — 21 skills, 359 files (byte-identical to Drive)

Every step below is **additive**. Back up `~/.claude` to `~/.claude/backups/pre-consolidate-<timestamp>/` before the first write.

---

## Sources: what to take from where

| Repo | Take | Skip |
|---|---|---|
| `Dobeu-tech-eco/dobeutech-claude-code-custom` | 20 agents, 20 commands, 8 rules, 10 skills, `plugin.json`. Merge the two unmerged branches (see Phase 7). | `hooks/hooks.json` verbatim — rewrite instead |
| `Dobeu-tech-eco/dobeu-composio-automate` | `CLAUDE.md` (automation-architect manual), `Append_system_prompt` | everything else |
| `dobeutech/claudeconfig` | `statusline-developer.sh` only | 38 third-party agents, dead n8n `settings.local.json` |
| `Dobeu-tech-eco/dobeu-claude-skills` | `frontend-design/` + `webapp-testing/` (the 2 skills missing locally) | rest — it's an unmodified mirror of `anthropics/skills` |
| `dobeutech/fk-everything-claude-code` | nothing | zero-commit fork of `affaan-m/ECC`; already the upstream of the custom repo |
| `dobeutech/claudecode-config` | nothing | raw `~/.claude` dump, 65% junk, **leaking live keys** |
| Google Drive backup | nothing | 10 months stale, Linux paths, already restored |

---

## Phase 0 — Security report (report only, no action)

Write `~/.claude/SECURITY_REMEDIATION.md`. Do **not** delete repos or revoke tokens — Jeremy rotates these himself.

Must cover:
1. `dobeutech/claudecode-config` (private) — live `GITHUB_PAT`/`GITHUB_TOKEN` (`ghp_…`), `OPENAI_API_KEY` (`sk-proj-…`), `NOTION_API_KEY` (`ntn_…`), `TAVILY_API_KEY` (`tvly-dev-…`) committed in `.env-mcp`, plus a committed `.credentials.json`. In git history permanently — only repo deletion removes it.
2. `G:\My Drive\ai-content\claudecode-config-global\claudecode-config\.claude\.env-mcp` — same keys plus `SNOWFLAKE_PASSWORD` and `MDB_MCP_CONNECTION_STRING`. This sits inside a **git repo on Drive**; confirm its remote was never pushed.
3. Live Composio `X-API-Key` in `~/.claude.json` under `projects["C:/Users/JeremyWilliams"].mcpServers.Composio.headers` and in all 5 `~/.claude/backups/*.backup.*` snapshots.
4. `dobeu-composio-automate/docs/plans/security-incidents/2026-04-25-doppler-vault-leak.md` documents a 24-credential prod vault leak marked **RISK-ACCEPTED, rotation declined**. The GitHub PAT appears on both exposure paths — flag that this makes the April "risk accepted" call worth revisiting.

Include rotation URLs per provider. Never print key values.

---

## Phase 1 — Agents: merge to 36

Source: `repos/dobeutech-claude-code-custom/agents/` → `~/.claude/agents/`

- Copy all 20 **except** `code-reviewer.md`.
- Keep the existing `~/.claude/agents/code-reviewer.md` (10 KB, richer than the repo's).
- Result: 36 agents. The existing 17 are untouched.

New agents gained: `accessibility-auditor`, `api-designer`, `architect`, `build-error-resolver`, `ci-cd-generator`, `database-migrator`, `deployment-manager`, `doc-updater`, `docker-specialist`, `e2e-runner`, `fullstack-architect`, `infrastructure-engineer`, `integration-tester`, `performance-tester`, `planner`, `refactor-cleaner`, `security-reviewer`, `tdd-guide`, `unit-test-generator`.

Sanity-check each copied file has valid frontmatter (`name`, `description`) — Claude Code silently ignores agents that don't.

---

## Phase 2 — Commands: install 17 of 20

Source: `repos/dobeutech-claude-code-custom/commands/` → `~/.claude/commands/` (currently empty).

**Three collide with Claude Code built-ins and must NOT be installed as-is:**

| File | Problem | Action |
|---|---|---|
| `login.md` | `/login` is a built-in — shadowing it breaks OAuth | **drop** |
| `plan.md` | `/plan` is built-in plan mode | **drop** |
| `code-review.md` | `/code-review` is a built-in skill | **rename** → `code-review-strict.md` |

Install the other 17 as-is: `/api-design`, `/audit-accessibility`, `/audit-performance`, `/audit-security`, `/build-fix`, `/changelog`, `/deploy`, `/docs-api`, `/docs-arch`, `/e2e`, `/migrate-db`, `/refactor-clean`, `/tdd`, `/test-coverage`, `/test-integration`, `/update-codemaps`, `/update-docs`.

6 of these are missing `description:` frontmatter on `main` (`build-fix`, `code-review`, `refactor-clean`, `test-coverage`, `update-codemaps`, `update-docs`). The `origin/commit` branch adds them — take the command files from that branch, not `main`.

---

## Phase 3 — Skills: 21 → 31

**3a. Convert 8 flat `.md` skills to loadable format.** Claude Code only loads `skills/<name>/SKILL.md`. These 8 are flat files and would be silently ignored:

`api-design-patterns`, `backend-patterns`, `clickhouse-io`, `coding-standards`, `database-patterns`, `frontend-patterns`, `memory-management`, `project-guidelines-example`

For each: create `~/.claude/skills/<name>/SKILL.md`, moving the body in and adding valid frontmatter (`name`, `description`). `project-guidelines-example.md` has **no frontmatter at all** — write one.

**3b. Copy the 2 already-correct skill dirs** as-is: `security-review/`, `tdd-workflow/`.

**3c. Add the 2 skills missing locally** from `repos/dobeu-claude-skills/skills/`: `frontend-design/`, `webapp-testing/`.

No name collisions with the existing 21.

---

## Phase 4 — Rules, CLAUDE.md, system prompt

- Copy all 8 `rules/*.md` → `~/.claude/rules/` (`agents`, `coding-style`, `git-workflow`, `hooks`, `patterns`, `performance`, `security`, `testing`).
- Also take **`rules/startup.md`** from the `origin/commit` branch — a 6-step session boot sequence (orient → assess → health check → session continuity → route-to-agent table → backend checks). It exists only on that branch.
- Fold `dobeu-composio-automate/CLAUDE.md` (the ~400-line automation-architect operating manual: 7-tier tool-routing tree, Composio session lifecycle, auth fallback cascade, multi-account routing, post-task automation delta review) into `~/.claude/CLAUDE.md` as a new section. **Append — do not overwrite.** The existing CLAUDE.md correctly documents the Windows environment and must survive.
- Save `dobeu-composio-automate/Append_system_prompt` → `~/.claude/system-prompts/append-system-prompt.md` (dir is currently empty).

---

## Phase 5 — Hooks: rewrite for Windows

The repo's `hooks/hooks.json` is unusable. Two independent problems:

1. **Invalid matcher syntax.** It uses `"matcher": "tool == \"Bash\" && tool_input.command matches \"…\""`. Real Claude Code matchers are a plain regex against the **tool name** (`"matcher": "Bash"`), with command filtering done inside the script against the JSON on stdin. As written these hooks never fire — on any OS.
2. **Linux-only + hostile.** All 11 commands are `#!/bin/bash` piping through `jq`. The tmux hook `exit 1`s on every `npm run dev` / `pnpm dev` / `yarn dev` / `bun run dev`. The `git push` hook calls blocking `read -r`, which hangs a non-interactive session.

**Write fresh PowerShell hooks into `~/.claude/settings.json`** (use the `update-config` skill — it owns settings.json edits). Correct shape:

```json
"hooks": {
  "PreToolUse": [
    { "matcher": "Bash", "hooks": [{ "type": "command", "command": "pwsh -NoProfile -File C:/Users/JeremyWilliams/.claude/hooks/pre-commit-secret-scan.ps1" }] }
  ],
  "PostToolUse": [
    { "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "pwsh -NoProfile -File C:/Users/JeremyWilliams/.claude/hooks/post-edit-format.ps1" }] }
  ]
}
```

Port these three, and only these three:

| Hook | Event / matcher | Behavior |
|---|---|---|
| `pre-commit-secret-scan.ps1` | PreToolUse / `Bash` | Read stdin JSON. If `tool_input.command` matches `git commit`, scan staged files for secret patterns (`api[_-]?key`, `secret`, `password`, `token`, `private[_-]?key` followed by a 20+ char value). Exit 1 to block on a hit. |
| `post-edit-format.ps1` | PostToolUse / `Edit\|Write` | If the edited path is `.ts/.tsx/.js/.jsx`, run `prettier --write` if prettier is on PATH; then `npx tsc --noEmit` scoped to that file's project if a `tsconfig.json` exists. Non-blocking — warn only. |
| `post-edit-console-log.ps1` | PostToolUse / `Edit\|Write` | Warn (never block) if `console.log` appears in the edited JS/TS file. |

**Explicitly DROP:** the tmux dev-server blocker, the `read -r` git-push pause, and the "block all `.md`/`.txt` writes" hook (it would block this very plan file).

Preserve the original `hooks/hooks.json` at `~/.claude/hooks/legacy-linux-hooks.json.reference` for provenance, clearly marked as non-functional.

---

## Phase 6 — Statusline

Take `statusline-developer.sh` from `dobeutech/claudeconfig` — the one genuinely hand-crafted artifact in that repo. It renders `model | output_style | project/relpath (branch +staged ~modified ?untracked) [HH:MM]`.

It uses `jq` and `realpath --relative-to` (GNU-only). **Rewrite as `~/.claude/statusline.ps1`** preserving the same output format, then register:

```json
"statusLine": { "type": "command", "command": "pwsh -NoProfile -File C:/Users/JeremyWilliams/.claude/statusline.ps1" }
```

---

## Phase 7 — MCP & plugins (low risk, mostly verification)

- **Do not touch** the 3 working stdio servers (`memory`, `sequential-thinking`, `Context7`) or the 22 claude.ai connectors. All 25 report Connected.
- Add a `github` MCP server — `gh` is already authed as `dobeutech`, so this was the only thing blocking it. Use `claude mcp add-json github … --scope user`, reading the token from a **user env var**, never inline.
- Save `mcp-configs/mcp-servers.json` (23 servers, all `YOUR_*_HERE` placeholders — no real secrets) to `~/.claude/mcp-catalog.json` as a reference menu. Fix the `filesystem` server's POSIX `/path/to/your/projects` → a Windows path.
- Delete the redundant `mcp_servers.scaffold.json` (a 4-server subset of `mcp-scaffold.json`).
- **`pluginUsage` in `~/.claude.json` shows 23 `@inline` plugins were in use pre-reset** — `beads`, `holocron`, `loki-mode`, `ruflo-core`, `subtask`, `wit`, `cartographer`, `hcom`, `agent-deck`, `skillfold`, `parallel`, `ralph-orchestrator`, and others. None are installed today. Report this list to Jeremy with what's re-installable from `anthropics/claude-plugins-official`; do not auto-install.

**Unrecoverable:** `prompts/` and `system-prompts/` were empty in every source. Nothing to restore beyond the Append_system_prompt in Phase 4.

---

## Phase 8 — Canonical repo (`dobeutech-claude-code-custom`)

Working from `C:\Users\JeremyWilliams\repos\dobeutech-claude-code-custom`. Do this on a branch, PR it, don't push straight to `main`.

Two branches contain unmerged work that would otherwise be lost:

1. **`origin/commit`** — v2.0.0, +14,694 lines. Multi-CLI generator architecture (claude/codex/gemini), `--dry-run` flag, `rules/startup.md`, command frontmatter fixes, and a `plugin.json` cleanup that removes 8 phantom skills listed but never written.
2. **`origin/feat/production-ready-…`** — adds `createBackup()` to the installer and a `claude-config uninstall` command.

Merge both, then apply these fixes:

- **Installer path bug:** `scripts/install.js` writes MCP config to `~/.claude/.claude.json`, but Claude Code reads `~/.claude.json` (home root). Fix the target.
- **Permission syntax:** `.claude/settings.json` uses legacy space-glob `Bash(git *)`. Current Claude Code wants `Bash(git:*)`. Convert.
- Replace `hooks/hooks.json` with the Windows PowerShell hooks from Phase 5 (keep the Linux ones in a clearly-labelled `hooks/legacy/` dir).
- Convert the 8 flat skills to `SKILL.md` dirs (same work as Phase 3a — do it once, in the repo, and have the installer copy the correct structure).
- Reconcile `plugin.json` against reality (it claims 17 skills; 8 don't exist. It omits `login`).
- Delete or fix `docs/sync-wsl.md` — it hardcodes the stale Windows username `jswil`; current user is `JeremyWilliams`.
- Add a `README` section documenting the Windows-first install path.

The npm package is `@jwdobeutechsolutions/dobeutech-claude-code-custom` (public, v1.0.3). Version-bump but **do not `npm publish`** without asking.

---

## Execution: parallel dispatch

Phases 1–4 and 6–7 are independent file copies with no shared writes. Dispatch as parallel agents:

- **Agent A** — Phases 1 + 2 (agents merge, commands install)
- **Agent B** — Phase 3 (skills: 8 flat→SKILL.md conversions + 4 dir copies)
- **Agent C** — Phases 4 + 6 (rules, CLAUDE.md append, system prompt, statusline.ps1)
- **Agent D** — Phase 5 (hooks rewrite — must own `settings.json` alone to avoid a write race)
- **Agent E** — Phase 0 (security report) + Phase 7 (MCP catalog, plugin report)

Phase 8 runs **after** all of the above land, since it consumes their outputs.

Serialize anything touching `settings.json`: only Agent D writes it during the parallel wave; the statusline key gets added by Agent D too, on input from Agent C.

---

## Verification

1. `~/.claude/backups/pre-consolidate-<ts>/` exists and contains the pre-change tree.
2. Launch `claude`, then check:
   - `/agents` → 36 agents listed, all with descriptions.
   - `/help` → the 17 new slash commands appear; `/login` and `/plan` still resolve to built-ins.
   - Skills list → 31 skills, including the 8 newly converted (a flat `.md` that failed conversion will simply be absent — that's the tell).
   - Statusline renders in the TUI with model, branch, and dirty-file counts.
3. `claude mcp list` → still 25 Connected, plus `github` if added.
4. `claude plugin list` → `composio@composio` v0.2.1 still enabled (proves settings.json wasn't clobbered).
5. **Hook smoke tests:**
   - `npm run dev` in any repo → **must NOT be blocked** (proves the tmux hook is gone).
   - Stage a file containing `api_key = "aaaaaaaaaaaaaaaaaaaaaaaa"`, attempt `git commit` → must be blocked by the secret scan.
   - Edit a `.ts` file → prettier/tsc warnings appear, and the edit is **not** blocked.
   - `git push` → completes without hanging (proves the `read -r` hook is gone).
6. `SECURITY_REMEDIATION.md` exists, names all 4+ leaked keys and their rotation URLs, and contains **zero key values**.
7. Repo: `git log --oneline` on the consolidation branch shows both source branches merged; `node scripts/install.js --dry-run` runs clean on Windows.
