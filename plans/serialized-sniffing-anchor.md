# Plan: Set up ruflo — general + tailored to this repo

## Context

You clarified that "run them all" meant **set up ruflo properly** — both in general and
specifically for this repo — not fire all 35 plugins. This session installed the ruflo
plugin suite and poked many commands ad-hoc, but ruflo was never actually *initialized*:
`doctor` reports **no config file**, the **auto-memory/learning-bridge hook is not installed**
(`npx ruflo init` never ran), **AIDefence isn't loadable**, and **encryption at rest is off**.
Meanwhile this session left three background token-consumers running and some working-tree
churn. This plan turns that ad-hoc state into a clean, intentional ruflo setup.

**Your four decisions (baked into this plan):**
1. **Install the always-on hooks** (full `ruflo init` with auto-memory/learning bridge).
2. **On-demand only** — stop the daemon, the audit cron, and the loop (loop already stopped).
3. **Enable encryption at rest** for the local stores + federation key.
4. **Disable off-domain plugins** (neural-trader, market-data, iot-cognitum, workflows/GAIA).

## Phase 1 — Quiet the background (stop the three consumers)

- **Loop** (testgaps+document+map): already stopped this turn.
- **Audit cron** `b0e51c0e`: `CronDelete`.
- **Daemon** PID 54388: `npx ruflo@latest daemon stop` (verify with `daemon status --all`).

Result: ruflo runs only when explicitly invoked.

## Phase 2 — General ruflo init (installs hooks + config)

- Run `npx ruflo@latest init` — installs the auto-memory/learning-bridge hooks (PreToolUse/
  PostToolUse/session hooks) and writes the ruflo **config file** the doctor says is missing.
- Run `npx ruflo@latest doctor --fix` to apply the 6 suggested fixes.
- Confirm the MCP server registration (`ruflo` is already in `.claude.json` per doctor) still resolves.
- **Optional (recommended for a payments app):** install `@claude-flow/aidefence` so the
  `aidefence_*` tools load (doctor flagged it unloadable).
- Verify the exact hook set written to `~/.claude/settings.json` / project settings after init;
  confirm nothing clobbers this repo's existing hooks.

## Phase 3 — Encryption at rest

- Enable encryption for the memory/session/federation-key stores (doctor: currently plaintext,
  mode 0600 only). **Exact mechanism to confirm at execution** — likely a ruflo `config set`
  security flag + a generated key; will read the ruflo security guidance / `doctor --fix`
  suggestion before running, and ensure the encryption key is stored outside git (the
  `.claude-flow/` tree is already gitignored).
- Re-run `doctor` to confirm "Encryption at Rest: On".

## Phase 4 — Tailor to this repo

- **Disable off-domain plugins:** `ruflo-neural-trader`, `ruflo-market-data`,
  `ruflo-iot-cognitum`, `ruflo-workflows` (GAIA), and `ruflo-arena`. Mechanism to confirm
  (`/plugin` disable vs. the enabledPlugins list in settings). Keep the relevant set:
  core, adr, ddd, docs, testgen, security-audit, migrations, metaharness, goals, cost-tracker,
  observability, jujutsu, rag-memory/agentdb/ruvector, intelligence, aidefence, loop-workers.
- **Align config to this project's `CLAUDE.md`:** hierarchical topology, max-agents, hybrid
  memory, and sensible memory namespaces (e.g. `patterns`, `horizons`, `adr-patterns`).
- **Reconcile federation identity:** keep the project node (`node-mrn3x7hw` under
  `.claude-flow/federation/`) and drop/ignore the stray global-bin node (`node-mrn4l49u`) so
  there's a single identity. (Federation transport remains non-functional via the isolated CLI —
  out of scope to fully fix here; documented.)

## Phase 5 — Clean up this session's residue

- **Revert lockfile churn** from the earlier agentic-flow add/remove:
  `git checkout -- package.json pnpm-lock.yaml` (after confirming devDeps match origin).
- **Global broken agentic-flow / midstreamer installs** (native scripts blocked, unused by the
  isolated CLI): optionally `npm rm -g agentic-flow midstreamer @claude-flow/plugin-agent-federation`
  to remove the ~900-package dead weight — or leave if you may wire federation later.
- **Decide on the legit edits made this session** (separate from ruflo setup): commit or keep in
  working tree — 4 ADRs (`docs/adr/ADR-001..004`), `CLAUDE.md` accuracy fixes, `.gitignore`
  secret-protection. (These are good changes; recommend committing.)
- **Deferred, safety-checked:** delete the `phase1-complete` duplicate tree + zip (~1.24 MB,
  contains a stray `.env.local`) — the refactor-cleaner verified it's an untracked, gitignored
  duplicate.

## Verification

- `npx ruflo@latest doctor` after setup shows: **Config File present**, **Learning Bridge /
  auto-memory hook installed**, **Encryption at Rest: On**, **Daemon: not running**.
- Background: `daemon status --all` shows none; `CronList` shows no audit cron; no loop wakeups.
- `/help` or the plugin list no longer surfaces the off-domain plugin commands/agents.
- `git status`: only the intended edits remain (ADRs/CLAUDE.md/.gitignore); `package.json` +
  `pnpm-lock.yaml` back to clean.
- Sanity: run one on-demand command (e.g. `/ruflo-core:ruflo-status`) and confirm memory hooks
  fire and store to the encrypted DB.

## Notes / risks

- The always-on hooks add token + latency overhead to **every** tool use going forward (your
  choice #1) — reversible later by re-running init without hooks or editing settings.
- A few exact mechanisms (encryption-enable command, per-repo plugin-disable) will be confirmed
  against ruflo's current CLI/docs at execution time rather than assumed — flagged inline above.
- Not touching production/Vercel or app code here — this is tooling setup only. The P0/P1/P2
  production-readiness roadmap remains tracked in the `horizons` memory namespace.
