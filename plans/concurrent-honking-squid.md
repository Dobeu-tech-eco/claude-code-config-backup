# Improve the workspace `CLAUDE.md`

## Context

`/init` was run at `C:\Users\JeremyWilliams`. A `CLAUDE.md` already exists here (248 lines,
12.1 KB), so the task is to improve it rather than create one.

Auditing it against the live system found that its **most load-bearing claims are now false**.
The harness moved from a project-scope `claude-flow` MCP registration to the `ruflo-core`
plugin, but `CLAUDE.md` still documents the old world. The single worst consequence is
concrete and measurable:

> `CLAUDE.md:224` states "The MCP tools stay `mcp__claude-flow__*` regardless."

That prefix matches nothing. The live prefix is `mcp__plugin_ruflo-core_ruflo__*`. Because
`~/.claude/settings.json` allowlists the dead `mcp__claude-flow__*` wildcard, **every ruflo MCP
call prompts for permission**, and `settings.local.json` has been silently accumulating one-off
grants (`wasm_agent_list`, `wasm_gallery_list`, `wasm_gallery_categories` are already there).

Intended outcome: every remaining claim in `CLAUDE.md` is verified true, the swarm sections are
trimmed to what isn't already in `~/.claude/rules/ruflo.md` (which loads every session anyway),
and the permission wildcard actually works.

## Evidence gathered

| Claim in CLAUDE.md | Reality |
|---|---|
| L103 "Live values come from the `env` block of `repos\.mcp.json`" | That file now contains **only** `brightdata`. No `claude-flow` entry, no `env` block. |
| L236-240 "`repos\.mcp.json` registers it at project scope, pinned to `ruflo@3.32.7`, carrying `CLAUDE_FLOW_CWD`" | Entry is gone. `.mcp.backup-20260724.json` shows it never used `3.32.7` — it used `ruflo@latest`, and carried no `CLAUDE_FLOW_CWD`. |
| L224 "MCP tools stay `mcp__claude-flow__*`" | Live server is `plugin:ruflo-core:ruflo` → `npx -y @claude-flow/cli@latest`; tools are `mcp__plugin_ruflo-core_ruflo__*`. |
| L17-19 "the stray 0-byte `repos\$null` file" | No longer exists. |
| L10 "workspace root, not a repository" | True at root, but `ruflo\`, `ruflo-memory\`, and `dts-contract-engine\` **are** git repos sitting at this level. |
| L13 "Code lives in `repos\<project>\`" | `dts-contract-engine` exists at **both** the root and `repos\` — no stated canonical copy. |
| L11 "root `package.json` has no `scripts`" | True, but it has real deps (`@composio/core`, `puppeteer-core`) plus **both** `package-lock.json` and `pnpm-lock.yaml` — the dual-lockfile state `repos\CLAUDE.md` onboarding gate #3 forbids. |
| L5-6 "AGENTS.md ... referencing agents that no longer exist" | Overstated — `agent-organizer`, `react-pro`, `typescript-pro`, `e2e-runner` all still exist. It's superseded, not dangling. |
| Config-layers table (4 layers) | Missing a 5th: `repos\.claude\skills\` auto-loads 36 directory-scoped skills under `repos\`. |
| — | `claude mcp list` warns: `Composio` is registered but `COMPOSIO_API_KEY` is missing. Global CLAUDE.md routes heavily through Composio. |

## Changes

### 1. `C:\Users\JeremyWilliams\CLAUDE.md` — corrections

- **Precedence note (L5-6):** soften the AGENTS.md rationale to "superseded by this file" rather
  than the false "agents no longer exist."
- **What This Directory Is (L10-19):** drop the `repos\$null` parenthetical; keep the
  PowerShell-vs-Bash rule. Add that `ruflo\`, `ruflo-memory\`, and `dts-contract-engine\` are git
  repos at this level, and flag the `dts-contract-engine` root-vs-`repos\` duplicate as
  unresolved. Note the root `package.json` carries deps + dual lockfiles despite having no
  `scripts`.
- **Config layers table (L26-31):** add the `repos\.claude\skills\` row.
- **Swarm Config (L101-113):** delete the `env`-block table entirely. Replace with the live
  fact: ruflo comes from the `ruflo-core` plugin running `@claude-flow/cli@latest`; swarm
  parameters are passed per-invocation, not read from `repos\.mcp.json`.
- **CLI naming note (L221-224):** correct the MCP-prefix sentence to
  `mcp__plugin_ruflo-core_ruflo__*`. Keep the `@claude-flow/cli` vs `ruflo` allowlist guidance —
  still accurate for `settings.json`.
- **Setup note (L232-240):** delete the entire "claude-flow legitimately appears at project
  scope" paragraph. Replace with: the plugin is the only source; if a `claude-flow` entry ever
  appears in `claude mcp list`, it is a duplicate to remove.
- **Portfolio commands (L202-205):** keep `ruflo@3.32.7` for memory-hub CLI commands (the hub at
  `repos\.swarm\memory.db` is real — verified), but drop the justification that ties the pin to
  the now-deleted `.mcp.json` registration. State it as a deliberate pin instead.

### 2. `CLAUDE.md` — trims (per "trim swarm guidance hard")

Remove or collapse; each duplicates `~/.claude/rules/ruflo.md` or is self-admittedly discoverable:

- **Agent Routing table (L115-123)** — delete. Topology is `hierarchical` in every row (zero
  information) and the agent names duplicate the Agents section.
- **MCP Tools table (L143-153)** — delete. The names lack the required plugin prefix, making the
  table actively misleading. Replace with one line: the prefix plus "discover via `ToolSearch`."
- **Background Workers table + dispatch (L155-167)** — collapse to a single line naming the
  triggers.
- **CLI Quick Reference (L207-219)** — cut to `doctor --fix` and `memory search`. The block
  already says "use `--help` on any command."
- **Agents section (L169-182)** — keep the `subagent_type` vs `agent_spawn` distinction (the
  genuinely non-obvious part, and the note at L76-80 depends on it); drop the exhaustive
  `agent_spawn` type enumeration.

Keep intact — verified correct and not covered elsewhere: the Rules list, the entire **Agent
Invocation (SendMessage-First)** section including the deferred-`SendMessage` warning and the
"no `run_in_background` on `Agent`" note, the Patterns table, When to Swarm, 3-Tier Model
Routing, and Build & Test.

Expected result: ~248 lines → ~150 lines, with every surviving claim verified.

### 3. `C:\Users\JeremyWilliams\.claude\settings.json` — fix the dead wildcard

- Add `mcp__plugin_ruflo-core_ruflo__*` to `permissions.allow`.
- Remove the dead `mcp__claude-flow__*` entry.

### 4. `C:\Users\JeremyWilliams\.claude\settings.local.json` — remove now-redundant grants

Delete the three one-off entries the new wildcard covers:
`mcp__plugin_ruflo-core_ruflo__wasm_agent_list`, `..._wasm_gallery_list`,
`..._wasm_gallery_categories`.

## Verification

1. **JSON still parses** (do this first — a broken settings file is silent):
   ```powershell
   Get-Content "$HOME\.claude\settings.json" -Raw | ConvertFrom-Json | Out-Null; "settings.json OK"
   Get-Content "$HOME\.claude\settings.local.json" -Raw | ConvertFrom-Json | Out-Null; "settings.local.json OK"
   ```
2. **Wildcard actually works** — the real test of the whole change. In a **new** session, call a
   ruflo MCP tool (e.g. `mcp__plugin_ruflo-core_ruflo__memory_search`) and confirm **no
   permission prompt** appears. Settings are read at session start, so the current session will
   not reflect the edit.
3. **No stale strings survive**:
   ```powershell
   Select-String -Path "$HOME\CLAUDE.md" -Pattern 'repos\\\$null|mcp__claude-flow__|CLAUDE_FLOW_TOPOLOGY|env. block of'
   ```
   Expect zero matches. `3.32.7` should match only in the memory-hub command row.
4. **MCP topology unchanged**: `claude mcp list` still shows `plugin:ruflo-core:ruflo` connected
   and no `claude-flow` entry.
5. **Layers table matches disk**: confirm `repos\.claude\skills\` exists and that skills from it
   appear in the session skill list when working under `repos\`.

## Follow-ups (flagged, not in scope)

- **Plaintext secret:** `repos\.mcp.backup-20260724.json` contains a raw BrightData token. The
  live `.mcp.json` correctly uses `${BRIGHTDATA_MCP_TOKEN}`; the backup was never sanitized.
  `repos\` is not a git repo, so it is not committed — but it is a token sitting on disk.
- **`COMPOSIO_API_KEY` missing** — `claude mcp list` flags it. Global CLAUDE.md routes external
  integrations through Composio first, so that routing is currently broken.
- **Duplicate `dts-contract-engine`** at root and `repos\` — needs a human decision on which is
  canonical before either is edited.
- **Dual lockfiles at workspace root** (`package-lock.json` + `pnpm-lock.yaml`) with
  `packageManager: pnpm@11.15.1` pinned — the portfolio's own onboarding gate #3 forbids this.
- **`/import` available:** both `.codex\config.toml` and `.gemini\settings.json` exist. Reply
  `/import` to scan what's importable (MCP servers, commands, subagents, skills, instructions),
  then `/import --yes=<digest>` to apply.
