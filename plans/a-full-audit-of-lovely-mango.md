# Full Audit & Streamline of `~/.claude` (Tools, Connectors, Hooks, Rules)

## Context

`C:\Users\JeremyWilliams\.claude` has grown organically across a Linux→Windows restore,
multiple marketplaces, and the Ruflo/ECC plugin suites. A read-only audit (3 parallel
Explore passes) found real duplication, contradictions, a plaintext secret, and no local
version control. The goal: **streamline, secure, and back up** the config so it is clean for
multi-agent orchestration and long agentic sessions while cutting context/latency burn.

Confirmed decisions from the user:
1. Duplicate agents/skills → **archive (reversible), don't delete**.
2. Plugins/MCP → **disable usageCount-0 plugins + dedupe connectors (native-first)**.
3. Hooks → **keep ecc as the quality layer, drop the overlapping PowerShell hooks, tame the friction gates**.
4. Backup → **git init in `~/.claude` + secret-safe `.gitignore` + scheduled auto-commit/push**.

All work happens under `C:\Users\JeremyWilliams\.claude\` (plus the one secret in the
home-level `.claude.json`). Every phase is ordered; do them top-to-bottom.

---

## Phase 0 — 🔴 SECURITY (do first)

**Findings**
- Plaintext Composio API key in `C:\Users\JeremyWilliams\.claude.json` →
  `projects["C:/Users/JeremyWilliams"].mcpServers.Composio.headers["X-API-Key"]` = `ck_wNN…` (**~line 2410**).
- Memory note `projects\C--Users-JeremyWilliams\memory\claude-config-restore-2026-07.md` records
  **four leaked API keys still awaiting rotation**.
- `.claude.json` also holds OAuth PII (email, org UUIDs, referral link ~lines 2237–2278).
- `.claude\backups\*.claude.json.backup.*` are full copies that **also contain the key + PII**.

**Actions**
1. **Rotate** the Composio key (user action, Composio dashboard) and rotate the four keys named
   in the memory note. Update that memory file's status once done.
2. Move the Composio key to an env var: `[Environment]::SetEnvironmentVariable("COMPOSIO_API_KEY","<new>","User")`,
   then set the header value in `.claude.json` to `${COMPOSIO_API_KEY}`.
3. Ensure `.claude.json`, `.credentials.json`, and `backups/` are **never** committed (see Phase 5 `.gitignore`).
4. The user's own `hooks\pre-commit-secret-scan.ps1` already blocks commit-time secrets — **keep it** (the one PowerShell hook we retain).

---

## Phase 1 — Hooks: keep ecc, drop duplicates, tame gates

Edit `C:\Users\JeremyWilliams\.claude\settings.json`.

**1a. Drop the two overlapping PowerShell PostToolUse hooks** (ecc already covers them):
- remove `post-edit-format.ps1` (dup of ecc `post:quality-gate` + `stop:format-typecheck`)
- remove `post-edit-console-log.ps1` (dup of ecc `post:edit:console-warn` + `stop:check-console-log`)
- **keep** the `PreToolUse/Bash` → `pre-commit-secret-scan.ps1` hook (security net, not duplicated).
- The dropped `.ps1` files stay on disk (archived, not deleted) so they're recoverable.

**1b. Tame the friction gates** — add to `settings.json → env` (surgical: keeps destructive-command
protection, removes the per-file/per-session fact-forcing friction hit this session):
```
"ECC_DISABLED_HOOKS": "pre:edit-write:gateguard-fact-force,pre:bash:gateguard-fact-force,pre:config-protection",
"GATEGUARD_BASH_ROUTINE_DISABLED": "1"
```

**1c. Fix `project-boundary@buildwithclaude`** (its `guard.sh` **fails closed** on Windows when
`cygpath`/`jq` are absent — this is what blocked work this session). Set
`"project-boundary@buildwithclaude": false` in `enabledPlugins`. Destructive-command coverage is
retained by ecc GateGuard + the secret-scan hook; re-enable later only if jq+cygpath are installed.

**1d. Trim always-on observability** (optional context/latency win): the six ecc `matcher:"*"`
hooks (`pre:observe`, `pre:mcp-health-check`, `post:session-activity-tracker`, `post:observe`,
`post:ecc-metrics-bridge`, `post:ecc-context-monitor`) spawn a node process on **every** tool call.
Add the ones you don't rely on to `ECC_DISABLED_HOOKS` above.

**1e. Remove the dead `enabledPlugins` entry** `"ruflo-graph-intelligence@ruflo"` (renamed to
`ruflo-knowledge-graph`; current entry resolves to nothing).

---

## Phase 2 — Plugins & MCP: disable unused, dedupe connectors

**2a. Disable usageCount-0 plugins** in `settings.json → enabledPlugins` (set `false`). Use
`.claude\plugins\installed_plugins.json` `usageCount` as the source of truth. Confirmed keepers:
`ecc`, `ruflo-core` (usage 440), `ruflo-cost-tracker` (48), `composio`, `context7`, `grok`, `vercel`,
`chrome-devtools` (ecc). Disable the 0-use bulk: the `agents-*@buildwithclaude` and
`commands-*@buildwithclaude` families, the `@inline` set (`firebase`, `supabase`, `laravel-boost`,
`telegram`, `prisma`, `mcp-notion`, `mcp-n8n`, `mcp-coingecko`, `google-analytics`, …), the ~30
unused `ruflo-*` sub-plugins, and `kegg`/`tlsradar`/`cashflow`/`fabler-relay` unless wanted. This is
the single biggest context/latency reduction. (`agent-drugs` is already disabled — leave it.)

**2b. Dedupe connectors — document a native-first routing rule** (matches existing CLAUDE.md policy).
Duplicate routes found: **Gmail, Calendar, Linear, Drive, Search** each reachable via 3–4 paths
(native + Composio + Make). Native claude.ai connectors are managed in the **Claude app UI** (not
`.claude.json`), so the file-level change is: keep the native connectors, and in CLAUDE.md state
"use native MCP for single-app reads/writes; Composio only for 2+ app chains; Make only for
persistent scheduled scenarios." Turn off redundant native connectors you don't use from the app's
connector settings.

**2c. Global MCP servers** (`.claude.json → mcpServers`): keep `Context7` (used) and
`sequential-thinking` (used). The `memory` knowledge-graph server is one of 4 memory backends —
decide its fate in Phase 4.

---

## Phase 3 — Agents & Skills: archive duplicates (reversible)

Create `C:\Users\JeremyWilliams\.claude\_archive\{agents,skills}\` and **move** (not delete) the
duplicates there so the loader stops picking them up but nothing is lost.

**3a. Agents** (`.claude\agents\`, 125 files today):
- Move the **~89 nested ruflo/claude-flow agents** (`core/ swarm/ consensus/ sparc/ github/
  flow-nexus/ templates/ v3/ sublinear/ optimization/ sona/ goal/ payments/ data/ development/
  documentation/ devops/ architecture/ analysis/ specialized/ testing/ browser/`) → archive; they
  duplicate the loaded `ruflo-core` plugin.
- Resolve the **4 real `name:` collisions** by archiving one of each pair: `planner.md` vs
  `core/planner.md`; `performance-engineer.md` vs `v3/performance-engineer.md`;
  `github/pr-manager.md` vs `templates/github-pr-manager.md`;
  `analysis/analyze-code-quality.md` vs `analysis/code-review/analyze-code-quality.md`.
- Among the 36 top-level, archive role-duplicates: `deployment-manager`↔`deployment-engineer`,
  `full-stack-developer`↔`fullstack-architect`, `performance-tester`↔`performance-engineer`,
  `unit-test-generator`↔`qa-expert`↔`test-automator`, `documentation-expert`↔`doc-updater`. Keep one
  of each. Agents that only duplicate an `ecc:*` skill can stay (different invocation surface).

**3b. Skills** (`.claude\skills\`, ~70 dirs): archive the clearly-redundant clusters —
- office/docs built-ins already shipped first-party (`pdf docx xlsx pptx canvas-design …`),
- the claude-flow build docs (`v3-*` set, `flow-nexus-*`, `swarm-*`, `sparc-methodology`, …),
- github skill set (dup of ecc/ruflo `github:*`),
- `skill-builder` (dup of `skill-creator`), `tdd-workflow` skill (dup of `tdd-guide` agent),
- the two non-skills with no `SKILL.md`: `skills\dual-mode\` and empty `skills\learned\`.
- **Memory skills** handled in Phase 4.

**3c. Fix stale count** — global `CLAUDE.md` says "17 specialized agent markdown files"; update after archiving.

---

## Phase 4 — Memory: pick one system of record

Four parallel backends today: native file-memory (`projects\C--Users-JeremyWilliams\memory\`),
MCP `memory` knowledge-graph, `mem0` (via skill), ruflo/AgentDB — plus two "unify memory" skills.

- **System of record = native file-memory** (`projects\C--Users-JeremyWilliams\memory\` + `MEMORY.md`);
  it is the one auto-loaded each session and is already curated.
- Archive the competing memory **skills** (`consolidate-memory`, `v3-memory-unification`,
  `memory-management`/mem0, `agentdb-memory-patterns`, `reasoningbank-agentdb`,
  `reasoningbank-intelligence`) into `_archive\skills\`.
- If the MCP `memory` knowledge-graph server is unused, remove it from `.claude.json → mcpServers`;
  ruflo keeps its own internal memory (leave it, it's plugin-scoped).
- Add a one-paragraph **memory policy** to global `CLAUDE.md` naming the file-memory as canonical.

---

## Phase 5 — Git backup with secret-safe `.gitignore` + auto-commit/push

**5a. Author `.gitignore`** at `.claude\.gitignore` BEFORE `git init`. Must exclude (secrets/PII/noise):
```
.credentials.json
backups/                # contains .claude.json backups with key + OAuth PII
*.backup.*
*-cache.json
daemon.status.json
stats-cache.json
gh-pr-status-cache.json
mcp-needs-auth-cache.json
.last-update-result.json
projects/**/todos/       # session transcripts / shell snapshots
shell-snapshots/
todos/
statsig/
plugins/cache/           # large, re-fetchable plugin caches
*.log
```
Keep tracked: `CLAUDE.md`, `settings.json`, `rules/`, `hooks/*.ps1`, `agents/` (retained),
`skills/` (retained), `_archive/` (so the archive is versioned), `projects/**/memory/`,
`mcp-catalog.json`, `mcp-scaffold.json`. Note: the home-level `.claude.json` sits **outside** this
repo, so its secret/PII is not captured — but keep it that way and never `git add` it.

**5b. Initialize & first commit** (`settings.local.json` already allows git commit/push):
`git init` in `.claude\`, `git add` per the ignore rules, initial commit. Verify with
`git status`/`git ls-files` that **no** secret/PII/cache file is staged before committing.

**5c. Remote + push** to the canonical repo (`Dobeu-tech-eco/dobeutech-claude-code-custom`, per the
memory note). Confirm the remote is **private** before first push (config carries machine paths).

**5d. Automate** — add a small `hooks\backup-commit.ps1` (git add/commit with timestamp, push if
remote reachable, fail-open) wired to a **Windows Scheduled Task** (e.g. hourly/daily) OR a
`Stop` hook in `settings.json`. Scheduled Task is preferred (doesn't add per-turn latency).

---

## Phase 6 — Reconcile CLAUDE.md & rules (staleness/contradiction)

- **Model tiers are outdated**: `rules\performance.md` recommends Haiku 4.5 / Sonnet 4.5 / Opus 4.5.
  Update to the current lineup (Opus 4.8, Claude 5 family, Haiku 4.5) so routing guidance is correct.
- **Two CLAUDE.md files** — global (374 ln) `.claude\CLAUDE.md` and home/Ruflo (180 ln) `~\CLAUDE.md`
  describe **two different agent systems** (global `agents/` catalog vs Ruflo swarm). Keep both but
  add a one-line cross-reference at the top of each stating which governs (global = defaults/routing,
  home = active project's swarm), and fix the stale "17 agents" line and any references to
  archived/removed pieces.
- Keep the `.pre-bootstrap.bak` files but note them as historical (don't let the broader
  `settings.local.json.pre-bootstrap.bak` allowlist get restored).

---

## Critical files to modify

- `C:\Users\JeremyWilliams\.claude.json` — Composio key → env var (Phase 0); maybe drop `memory` server (Phase 4).
- `C:\Users\JeremyWilliams\.claude\settings.json` — hooks, env gate-taming, enabledPlugins pruning (Phases 1–2).
- `C:\Users\JeremyWilliams\.claude\CLAUDE.md` + `C:\Users\JeremyWilliams\CLAUDE.md` — reconcile (Phase 6).
- `C:\Users\JeremyWilliams\.claude\rules\performance.md` — model tiers (Phase 6).
- New: `.claude\.gitignore`, `.claude\hooks\backup-commit.ps1`, `.claude\_archive\` (Phases 3–5).
- Reuse existing: `hooks\pre-commit-secret-scan.ps1` (keep), `installed_plugins.json` (read for usageCount).

## Verification

1. **Secret gone**: `Select-String ck_ C:\Users\JeremyWilliams\.claude.json` returns nothing but the `${COMPOSIO_API_KEY}` ref; Composio MCP still connects (`claude mcp list`).
2. **Hooks**: start a fresh session — no GateGuard fact-forcing denial on first Edit/Bash, no project-boundary block on a Windows path; a `.ts` edit produces **one** console.log/format pass, not 3–4.
3. **Plugins**: `claude` starts cleanly; disabled plugins' tools no longer appear; kept tools (ecc, ruflo-core, Context7, vercel) still work.
4. **Agents/skills**: archived items no longer listed by the agent/skill picker; `_archive\` holds them; no `name:` collision warnings.
5. **Git backup**: `git -C C:\Users\JeremyWilliams\.claude ls-files` shows **no** secret/PII/cache path; `git log` has the initial commit; the scheduled task fires and pushes; remote repo is private.
6. **Docs**: CLAUDE.md counts/model tiers match reality; memory policy present.
