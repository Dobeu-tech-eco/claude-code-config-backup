# Revise `C:\Users\JeremyWilliams\CLAUDE.md`

## Context

`/init` was run in `C:\Users\JeremyWilliams`. This is **not a repository** — it's the Windows
workspace root (`git status` → "not a git repository"). Actual code lives in
`C:\Users\JeremyWilliams\repos\<project>`. So there is no codebase to document, and the standard
`/init` deliverable (build/test commands + architecture) does not apply here.

A `CLAUDE.md` already exists (7.6 KB, "Ruflo — Claude Code Configuration"). It is a *workspace
operating config*, and that is the right thing for this location. The problem is that several of its
instructions are verifiably wrong against the current machine state, and a future session that
follows them will call a non-existent tool parameter, re-create an MCP duplicate that was already
fixed once, and run a build command that cannot succeed here.

**Goal:** correct the wrong parts, remove what duplicates `~/.claude/rules/ruflo.md`, and add the
missing "what this directory is" orientation — without changing the file's intent or growing it.

**Decision taken:** "Correct + restructure" (user-selected).

---

## Verified findings

Each of these was checked against disk, not inferred.

| # | Finding | Evidence |
|---|---------|----------|
| 1 | **`run_in_background: true` is not a parameter of the `Agent` tool.** The "Agent Comms" section passes it in all 5 spawn examples and states it as a rule. | Agent tool schema accepts only `description`, `prompt`, `subagent_type`, `model`, `name`, `isolation`, `mode`. Subagents already run in the background by design. |
| 2 | **The Setup block recreates a duplicate MCP server.** It instructs `claude mcp add claude-flow -- npx -y ruflo@latest mcp start`. | `.claude.json → mcpServers` contains only `memory`, `sequential-thinking`, `Context7`, `devfleet`, `GitKraken`. The `mcp__claude-flow__*` tools come from the **`ruflo-core` plugin**. Global memory already records "ruflo MCP dedup" as a past cleanup — this block would undo it. |
| 3 | **`npm run build && npm test` cannot run at this path.** Stated as an unconditional "Build & Test" rule. | Root `package.json` has `dependencies` + `packageManager` only — **no `scripts` block**. |
| 4 | **`SendMessage` is a deferred tool.** The Agent Comms protocol is built entirely on it but never says it must be loaded first. | `SendMessage` appears in the deferred-tools list; calling it directly fails with `InputValidationError` until `ToolSearch("select:SendMessage")` runs. |
| 5 | **Two CLI package names for one tool, unexplained.** `npx @claude-flow/cli@latest` (Memory & Learning, CLI Quick Reference) vs `npx ruflo@latest` (Setup). | Both appear in the same file. `.claude/settings.json` allowlists `Bash(npx @claude-flow*)` and `PowerShell(npx @claude-flow/cli@latest hooks worker dispatch ...)`. |
| 6 | **The Agents section conflates two different namespaces.** It lists `coder`, `reviewer`, `tester`, `planner`, `researcher`, `system-architect`… and says "Any string works as a custom agent type" — true for ruflo's `agent_spawn` MCP tool, **false** for Claude Code's `Agent` tool. The JS example then feeds those bare names to `Agent({subagent_type: ...})`. | Registry exposes `ruflo-core:coder`, `ruflo-core:researcher`, `ruflo-core:reviewer`, `ruflo-swarm:architect`, `ruflo-testgen:tester` — no bare equivalents. |
| 7 | **Model routing table is stale.** Tier 3 reads "Sonnet/Opus"; `~/.claude/rules/performance.md` still describes "Opus 4.8 / Claude 5 family". | Session model is **Opus 5** (`claude-opus-5[1m]`). |
| 8 | **Duplication with global rules.** "Memory & Learning" and "When to Swarm" restate `~/.claude/rules/ruflo.md`, which already auto-loads every session — and the file's own Rules section already links to it. | Both files present in session context simultaneously. |
| 9 | **No orientation section.** Nothing says this is the workspace root, that code is in `repos/`, or that `G:\My Drive\...` is the config backup target. | Absent from the file. |

### Out of scope but worth knowing

- **`~/.claude/agents/` is empty — 0 `.md` files, recursively.** The global `~/.claude/CLAUDE.md`
  claims "31 active agent markdown files" and `~/.claude/rules/agents.md` documents a whole flat
  roster (`planner`, `architect`, `tdd-guide`, `code-reviewer`, `security-reviewer`, `python-pro`,
  `automation-architect`, `memory-curator`, …). None of them exist or appear in the session's agent
  registry. Those are *global* files, not the one `/init` targets — flagging, not fixing.
- **`C:\Users\JeremyWilliams\AGENTS.md`** is a legacy Grok "7-checkpoint autonomous loop" that
  references agents the global config itself calls archived (`unit-test-generator`, `qa-expert`) and
  prescribes a worktree protocol contradicting CLAUDE.md's swarm rules. **I will not touch this
  file** — only add one line to CLAUDE.md establishing precedence.
- No `.cursorrules`, no `.cursor/rules/`, no `.github/copilot-instructions.md` — nothing to fold in.
  (`.cursor/` holds only plans, `mcp.json`, and extensions.)

---

## Assumptions on the two unanswered questions

Stated explicitly so they're easy to override:

- **CLI naming → document both.** Command examples keep `npx @claude-flow/cli@latest`, because that
  is what `.claude/settings.json` already allowlists (switching would introduce fresh permission
  prompts on every command). One line added noting `ruflo` is the same tool under its newer name.
- **AGENTS.md → pointer only.** One precedence line in CLAUDE.md; `AGENTS.md` itself is left byte-for-byte alone.

---

## Target structure for `CLAUDE.md`

Only file modified: **`C:\Users\JeremyWilliams\CLAUDE.md`**.

```
1. Scope & Precedence        (keep; extend with AGENTS.md precedence line)
2. What This Directory Is    (NEW — orientation)
3. Rules                     (keep; trim commit-trailer rule)
4. Agent Invocation          (REWRITE of "Agent Comms" — this is where the bugs are)
5. Swarm & Routing           (keep config + routing table; cut duplicated when-to-swarm prose)
6. Memory & Learning         (collapse to MCP tool table + pointer to rules/ruflo.md)
7. Build & Test              (rewrite as per-repo, not universal)
8. CLI Quick Reference       (keep; add the naming note)
9. Setup                     (rewrite — remove the duplicate-MCP instruction)
```

### Section 2 — What This Directory Is (new, ~8 lines)

State plainly: workspace root, not a repo; code lives in `repos/<project>` and each has its own
`CLAUDE.md` that wins there; `_staging/`, `_standards/`, `_to_delete/` are holding areas; config
backup target is `G:\My Drive\ai-content\claudecode-config-global\`; shell is PowerShell 7.

### Section 4 — Agent Invocation (rewrite)

Fixes findings 1, 4, and 6. The corrected spawn example:

```javascript
// Load SendMessage before any agent that will use it — it is a deferred tool.
ToolSearch({ query: "select:SendMessage", max_results: 5 })

// All agents in ONE message so they run concurrently. No run_in_background flag exists.
Agent({ name: "researcher", subagent_type: "ruflo-core:researcher",
        description: "Research codebase",
        prompt: "Research <X>. When done, SendMessage your findings to 'architect'." })
Agent({ name: "architect",  subagent_type: "ruflo-swarm:architect",
        description: "Design solution",
        prompt: "Wait for a message from 'researcher'. Design the solution, SendMessage to 'coder'." })
Agent({ name: "coder",      subagent_type: "ruflo-core:coder", ... })
Agent({ name: "tester",     subagent_type: "ruflo-testgen:tester", ... })
Agent({ name: "reviewer",   subagent_type: "ruflo-core:reviewer", ... })

SendMessage({ to: "researcher", summary: "Start", message: "<task context>" })
```

Plus an explicit namespace note: plugin-prefixed names (`ruflo-core:*`, `ecc:*`) are for the
**`Agent` tool**; bare strings like `"backend-dev"` are for the **ruflo `agent_spawn` MCP tool** and
do not resolve as `subagent_type`. Keep the Pipeline / Fan-out / Supervisor table and the
"spawn all in one message, then stop and report" rule — both are correct and useful.

### Section 7 — Build & Test (rewrite)

Replace the unconditional `npm run build && npm test` with: run the *project's* verification command
from within `repos/<project>`; read its `package.json` scripts (or `Cargo.toml`/`pyproject.toml`)
first; the workspace root has no build. Preserves the intent (never claim done unverified) without
prescribing a command that fails here.

### Section 9 — Setup (rewrite)

Drop `claude mcp add claude-flow -- npx -y ruflo@latest mcp start` entirely. Replace with: ruflo MCP
tools are provided by the **`ruflo-core` plugin** — do not add a standalone `claude-flow` MCP server,
it duplicates the plugin. Keep `npx ruflo@latest doctor --fix` and the existing daemon caveat (that
caveat is accurate and valuable — leave its wording intact).

### Trims

- "When to Swarm" YES/NO list → one line pointing at `~/.claude/rules/ruflo.md` (already linked in Rules).
- "Before Any Task" / "After Success" bash blocks → fold into the MCP tools table; the rules file covers the discipline.
- Model routing tier 3: "Sonnet/Opus" → "Opus 5 / Sonnet 5".

---

## What I will not do

- Not touch `AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.claude/rules/*`, or `settings.json`.
- Not delete any file.
- Not add build/lint/test commands for `repos/*` projects — those belong in each project's own `CLAUDE.md`.
- Not repair the empty `~/.claude/agents/` roster (separate decision, flagged above).

---

## Verification

1. `git diff` is unavailable (not a repo) → compare against a pre-edit copy in the scratchpad and
   confirm only the intended sections changed.
2. Re-check every command the revised file prescribes actually resolves:
   - `npx @claude-flow/cli@latest --version`
   - confirm `.claude.json → mcpServers` still has **no** `claude-flow` entry after following Setup.
3. Confirm each `subagent_type` named in the file appears in the session's agent registry
   (`ruflo-core:researcher`, `ruflo-swarm:architect`, `ruflo-core:coder`, `ruflo-testgen:tester`,
   `ruflo-core:reviewer`).
4. Smoke-test the corrected spawn pattern with **two** agents (researcher → architect) rather than
   five, and confirm `SendMessage` resolves after `ToolSearch`.
5. Confirm the file still parses as clean Markdown and stayed at or below its current 7.6 KB.

---

## Follow-up to raise separately

- `~/.claude/agents/` is empty while global config documents 31 agents — the global roster docs are
  describing something that isn't installed.
- `~/.codex/` and `~/.gemini/` configs are present and importable. Reply **`/import`** to scan and
  list what's importable (MCP servers, slash commands, subagents, skills, instructions), then
  `/import --yes=<digest>` to apply. I have deliberately not read those files.
