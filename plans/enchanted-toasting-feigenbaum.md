# Plan: Improve the workspace CLAUDE.md files

## Context

`/init` was run at `C:\Users\JeremyWilliams`. A `CLAUDE.md` already exists here, so the task is
improvement, not creation.

Exploration turned up one problem worth more than everything else combined: **there are two
CLAUDE.md files in the load path and they contradict each other.**

- `C:\Users\JeremyWilliams\CLAUDE.md` (214 lines) — current, corrected.
- `C:\Users\JeremyWilliams\repos\CLAUDE.md` (214 lines) — an **older fork of the same file**, plus
  ~60 lines of unique portfolio content appended.

When work happens in `repos\<project>\`, Claude Code loads both. The root file's own precedence rule
says "the more specific file wins" — so the *stale* fork wins, and it re-asserts four things the root
file explicitly documents as **broken**:

| `repos\CLAUDE.md` says | Root `CLAUDE.md` says |
|---|---|
| `Agent({ …, run_in_background: true })` | "There is **no** `run_in_background` parameter on `Agent`" |
| `subagent_type: "coder" / "system-architect" / "tester"` | Bare strings are `agent_spawn` MCP types; they **do not resolve** as `subagent_type` |
| "Any string works as a custom agent type" | Must match the registry: `ruflo-core:*`, `ruflo-swarm:*`, `ecc:*`, `Explore`, `Plan` |
| `claude mcp add claude-flow -- npx -y ruflo@latest mcp start` | "**Do NOT** run `claude mcp add claude-flow`" — it duplicates the plugin |
| `npm run build && npm test` (universal) | No workspace build; read the project's own `package.json` |
| Max Agents: 15 | Max Agents: 20 |

Intended outcome: one source of truth per topic, no duplicated prose left to drift, and the root file
corrected against what the machine actually reports.

**Assumption (flip at approval if wrong):** resolve by *slimming* `repos\CLAUDE.md` to its unique
content and keeping both files, rather than merging everything up into root. Rationale: the portfolio
rules only apply under `repos\`, and root already loads in every session — merging would tax every
unrelated session with ~60 lines of repo-onboarding detail.

---

## Verified facts (checked this session, not assumed)

| Claim | Status |
|---|---|
| `C:\Users\JeremyWilliams` is not a git repo | ✅ `git rev-parse` → *fatal: not a git repository* |
| Root `package.json` has no `scripts` | ✅ only `dependencies` + `packageManager` (pnpm 11.15.1) |
| `repos\.swarm\memory.db` is the single hub | ✅ exists, 811 KB, + `hnsw.index` 1.6 MB |
| `repos\.mcp.json` carries `CLAUDE_FLOW_CWD` | ✅ set to `C:\Users\JeremyWilliams\repos` |
| Pinned ruflo version | ✅ `ruflo@3.32.7`, `autoStart: false` |
| `CLAUDE_FLOW_MAX_AGENTS` | ⚠️ **15** — root CLAUDE.md claims 20 |
| `claude-flow` absent from `claude mcp list` | ❌ **present and Connected**, alongside `plugin:ruflo-core:ruflo` |
| `_standards\checks\check-amplitude.mjs` | ✅ exists |
| `ruflo-session-end.bat`, `ruflo-monthly-maintenance.bat` | ✅ exist at `repos\` root |
| `.claude\settings.json` has `attribution` / `includeCoAuthoredBy` | ❌ neither key present |
| Cursor / Copilot rule files | ❌ none (`.cursor\` is IDE state; no `.cursorrules`, no `.github\copilot-instructions.md`) |
| Root `README.md` | ❌ none |

---

## Changes

### 1. `C:\Users\JeremyWilliams\repos\CLAUDE.md` — cut to unique content

Delete the sections duplicated from root: *Agent Comms*, *Swarm & Routing*, *Memory & Learning*
(the CLI-command half), *Agents*, *Build & Test*, *CLI Quick Reference*, *Setup*, and the top *Rules*
block. Target ≈70 lines, down from 214.

Keep, verbatim, the three sections that exist nowhere else:

- **Portfolio Memory Hub (Enforced — 2026-07-24)** — one hub at `repos\.swarm\memory.db`; namespace =
  repo folder name; every repo has a `project-card` key to read *before* working in it; the
  `claude-memories` and `knowledge-graph` namespaces; the `CLAUDE_FLOW_CWD` requirement; the gotchas
  (`adaptive` is not a valid topology · always `-f json` on export · daemon holds a WAL lock · stale
  0-byte `-wal`/`-shm` sidecars block writes · never put `> < & |` in keys — cmd.exe eats them).
- **Repo Onboarding Gates (Enforced — 2026-07-24)** — the six gates for any new/cloned repo.
- **Analytics Instrumentation (Amplitude)** — rubric, `check-amplitude.mjs`, key-env-var names.

Replace the deleted material with a two-line header:

```markdown
# Ruflo Portfolio — `repos\` scope

> Swarm, agent invocation, model routing, CLI, and build/test policy live in the root
> `C:\Users\JeremyWilliams\CLAUDE.md`. This file adds **portfolio-only** rules for `repos\`
> and never restates root. Each `repos\<project>\CLAUDE.md` wins inside its own project.
```

### 2. `C:\Users\JeremyWilliams\CLAUDE.md` — correct the drift

- **Max Agents** — change `20` to `15`, and note the value is set by
  `CLAUDE_FLOW_MAX_AGENTS` in `repos\.mcp.json` (edit there, not here).
- **The `claude mcp add claude-flow` warning** — the rule is right but its verification step is wrong.
  `claude-flow` *does* appear in `claude mcp list`, legitimately: `repos\.mcp.json` registers it at
  project scope, pinned to `ruflo@3.32.7`, because it is the only registration carrying
  `CLAUDE_FLOW_CWD` (without it the server binds System32 and sees an empty store). Reword to: never
  add a **user-scope** `claude-flow`; the project-scope entry in `repos\.mcp.json` is intentional —
  and the thing to check for is a *second, unpinned* entry, not any entry at all.
- **Add a "Config layers" line** under *What This Directory Is*, naming the middle layer explicitly:
  `~/.claude/CLAUDE.md` (global) → this file (workspace) → `repos\CLAUDE.md` (portfolio) →
  `repos\<project>\CLAUDE.md` (project). Each tightens, never loosens.

### 3. `C:\Users\JeremyWilliams\CLAUDE.md` — add the commands that actually exist

`/init` asks for build/lint/test. Root correctly says there is no workspace-root build; it should also
say what *does* run at this level. Extend the **Build & Test** section:

```markdown
There is no workspace-root build. Inside `repos\<project>\`, read that project's `package.json`
scripts (or `Cargo.toml` / `pyproject.toml`) before assuming `npm run build && npm test`.

Portfolio-level commands (run from `repos\`):

| Command | Purpose |
|---|---|
| `node _standards\checks\check-amplitude.mjs <repo-path>` | Amplitude gate; exit 1 = violation |
| `.\ruflo-session-end.bat` | hooks post-task + consolidate — the learning signal |
| `.\ruflo-monthly-maintenance.bat` | export backup → compress → cleanup |
| `npx -y ruflo@3.32.7 memory search --namespace <repo> "project card"` | read a repo's card before working in it |

Use the pinned `ruflo@3.32.7`, not `@latest` — the hub schema is pinned to it.
```

### 4. Security — move the BrightData token out of `repos\.mcp.json`

`repos\.mcp.json` embeds a live token in the server URL:
`https://mcp.brightdata.com/mcp?token=<token>&pro=1`

`repos\` is not a git repo, so this is not committed — but it is plaintext, and the documented config
backup target is `G:\My Drive\ai-content\claudecode-config-global\`. Per the global Auth & Secrets
rule, move it to a user env var and reference it:

```powershell
[Environment]::SetEnvironmentVariable("BRIGHTDATA_MCP_TOKEN","<token>","User")
```

Then rotate the exposed token at BrightData. (Related: memory `claude-config-restore-2026-07` still
lists four leaked API keys awaiting rotation — worth clearing in the same pass.)

### 5. Housekeeping

`repos\$null` is a stray 0-byte file — the artifact of a `2>$null` redirect run under Bash instead of
PowerShell. It is concrete evidence for the existing shell-syntax rule; cite it there in one clause
and delete the file.

### 6. Offer `/import` for the other agent configs

Both `~\.codex\config.toml` and `~\.gemini\settings.json` exist. Per `/init` protocol I will not read
or convert them. Tell the user: reply **`/import`** to scan and list what's importable (MCP servers,
slash commands, subagents, skills, instructions), then **`/import --yes=<digest>`** — the scan output
names the digest — to apply the user-level items. If `/import` isn't available on this surface, run
`claude import` from a terminal.

---

## Not doing (and why)

- **No Cursor/Copilot rule import** — none exist. `.cursor\` holds IDE session state only; there is no
  `.cursorrules`, no `.cursor\rules\`, no `.github\copilot-instructions.md`.
- **No README section** — there is no root `README.md` to draw from.
- **Not touching `AGENTS.md`** — root CLAUDE.md already marks it a legacy Grok protocol not to follow.
- **Not touching `~\.claude\rules\*.md`** — out of `/init` scope. One inaccuracy noted for later:
  `rules\git-workflow.md` claims "Attribution disabled globally via ~/.claude/settings.json", but
  `settings.json` has neither `attribution` nor `includeCoAuthoredBy`. The CLAUDE.md rule (never add
  the trailer unless `attribution.commit` is set) is correct as written and needs no change.

---

## Verification

1. **No contradictions remain** — grep the slimmed file for the six stale patterns; each must return zero:
   ```powershell
   cd C:\Users\JeremyWilliams\repos
   Select-String -Path CLAUDE.md -Pattern 'run_in_background','system-architect','claude mcp add','npm run build','Max Agents','Any string works'
   ```
2. **No duplication left** — the only headings shared between root and `repos\CLAUDE.md` should be none;
   compare heading sets:
   ```powershell
   $a = Select-String -Path C:\Users\JeremyWilliams\CLAUDE.md -Pattern '^#{1,3} ' | % { $_.Line }
   $b = Select-String -Path C:\Users\JeremyWilliams\repos\CLAUDE.md -Pattern '^#{1,3} ' | % { $_.Line }
   Compare-Object $a $b -IncludeEqual | ? SideIndicator -eq '=='
   ```
3. **Corrected facts match the machine:**
   - `Select-String -Path repos\.mcp.json -Pattern 'MAX_AGENTS'` → 15, matching root CLAUDE.md.
   - `claude mcp list | Select-String 'claude-flow'` → exactly one entry, pinned `ruflo@3.32.7`.
4. **Commands are real** — each Build & Test table entry resolves:
   ```powershell
   Test-Path repos\_standards\checks\check-amplitude.mjs, repos\ruflo-session-end.bat, repos\ruflo-monthly-maintenance.bat
   ```
5. **Token gone** — `Select-String -Path repos\.mcp.json -Pattern 'token='` returns no literal secret,
   and `claude mcp list` still shows brightdata Connected via the env var.
6. **Live read-back** — start a fresh session inside a `repos\<project>\` directory and confirm the
   loaded context shows root + slimmed portfolio file with no conflicting agent-invocation guidance.
