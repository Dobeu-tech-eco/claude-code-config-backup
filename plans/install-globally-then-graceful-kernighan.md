# Plan: Finish AgentBox setup + dedupe/verify Ruflo, then ship a usage tutorial

## Context

You asked me to install `@madarco/agentbox`, run `agentbox install`, wire it up so **all
features are accessible** (with agents launching in plan/`writing-plans` mode so you approve
their work), integrate **Grok / Codex / Claude Code and everything else it works with**, do the
same for **Ruflo** (already available as a plugin), set it up globally, and write a tutorial.

Investigation shows **most of this is already installed** on this Windows 11 host — so the real
work is *targeted integration, cleanup, and a tutorial*, not a fresh install:

| Component | Current state |
|---|---|
| `@madarco/agentbox` | **v0.26.1 installed globally — already the latest on npm** (`npm -g i` = no-op) |
| `agentbox install` | **Already run** — `~/.agentbox/setup-complete.json`, `docker-prepared.json`, relay running (`relay.pid`), `config.yaml` (portless on) |
| `/agentbox` host skill | Present at `~/.claude/skills/agentbox` (+ `agentbox-info`) |
| Docker / gh | Docker 29.6.1 running; `gh` 2.96.0 authed as `dobeutech` (HTTPS) → relay pushes/PRs work |
| Agent CLIs on host | claude 2.1.208 ✓, codex 0.144.3 ✓, grok 0.2.101 ✓, gemini 0.50.0 ✓, **opencode ✗** |
| Ruflo | **v3.32.0 global (latest)** + plugin cache with all sub-plugins + MCP connected |
| Ruflo MCP | **Registered TWICE** — `plugin:ruflo-core:ruflo` *and* standalone `ruflo` (redundant tool surface) |

**Key correction to the request:** AgentBox only runs **Claude / Codex / OpenCode** *inside*
boxes. It does **not** run Grok or Gemini in a box. Those two are already integrated into Claude
Code a different way — the `grok` MCP plugin is connected and `grok:rescue` / `gemini:rescue` /
`codex:rescue` skills exist. The plan handles each in its correct lane.

### Decisions confirmed
- In-box agents: **Claude + Codex + OpenCode**
- Providers: **Docker (done) + E2B + Vercel**
- Ruflo MCP: **dedupe, keep the `ruflo-core` plugin**, remove the standalone
- Tutorial: **HTML Artifact**

---

## What I'll do (after approval)

Steps I run are marked **[me]**; steps needing interactive auth you run in-session with the `!`
prefix are marked **[you `!`]**.

### 1. Confirm versions (honor the literal request; no-op expected)
- **[me]** `npm -g i @madarco/agentbox` and `npm -g i ruflo` — both already latest, so this just
  confirms nothing is partially installed. Skips if unchanged.

### 2. AgentBox — wire the remaining in-box agents & features
- **[me]** `agentbox install codex` — adds + enables the AgentBox Codex plugin (marketplace add,
  plugin add, enables it by default in `~/.codex/config.toml`). This is the concrete
  "integrate codex" step.
- **[me]** Install OpenCode CLI on host: `npm -g i opencode-ai@latest`, then confirm
  `agentbox opencode --help` resolves.
- **[me]** `agentbox install --skills-only --force` — re-assert the host `/agentbox` fork skill
  files are current (idempotent).
- **[me] plan-mode default (the `/writing-plans` ask):** set boxed agents to launch in plan mode
  so they draft plans you approve. Set via `agentbox config set` (e.g. a `defaults:` passthrough)
  and/or document the `agentbox claude -- --permission-mode=plan` form. I'll confirm the exact
  config key with `agentbox config list --all` before writing, then verify with
  `agentbox agent get-plan-question` / `agent approve` in the smoke test.

### 3. AgentBox — cloud providers (E2B + Vercel)
- **[you `!`]** `! agentbox install --provider e2b` — interactive: logs into E2B (needs an
  `E2B_API_KEY` from e2b.dev) and builds the base template.
- **[you `!`]** `! agentbox install --provider vercel` — interactive: Vercel login + prepare.
- **[me]** After each, verify with `agentbox prepare` (no `--provider` prints status across all
  providers) and record which are `prepared`.

### 4. AgentBox — smoke test end-to-end **[me]**
- `agentbox claude -i "print the working dir and list top-level files, then stop"` (Docker,
  background queue), then drive it headlessly:
  `agentbox agent wait-for input-needed <box> --timeout 600000` →
  `agentbox agent get-plan-question`/`drive snapshot` → `agentbox queue wait-for empty-queue`.
- Confirms: box creation, in-box agent launch, plan-mode gating, relay, queue draining.
- Tear down with `agentbox destroy`.

### 5. Grok / Gemini / Codex inside Claude Code (the non-agentbox lane) **[me]**
- Verify the `grok` MCP plugin is connected (it is) and the `grok:setup`, `codex:setup`,
  `gemini:setup` skills report ready; run each `:setup` check. Any that need auth →
  **[you `!`]** run the login the skill prints. This is what "integrate grok … into the system"
  means in practice, since Grok can't run in an agentbox box.

### 6. Ruflo — dedupe, health-check, verify
- **[me]** `claude mcp list` → confirm the standalone `ruflo` scope, then
  `claude mcp remove ruflo` (removes the redundant standalone; the managed
  `plugin:ruflo-core:ruflo` stays). Re-run `claude mcp list` to confirm exactly one ruflo entry.
- **[me]** `npx ruflo@latest doctor --fix` — repairs/validates the global install & plugin wiring.
- **[me]** Sanity-check a couple of ruflo MCP tools still resolve after dedupe (e.g.
  `mcp__plugin_ruflo-core_ruflo__system_status`).
- Note: the optional token-burning `ruflo daemon` stays **off** (per project CLAUDE.md).

### 7. Tutorial — HTML Artifact **[me]**
- First load the `artifact-design` skill (required before authoring), then build a single-page,
  theme-aware, self-contained Artifact covering:
  - **AgentBox:** mental model (box + host relay), the two entry commands (`create`, `claude`),
    `-i` background fan-out, the `drive` / `agent wait-for input-needed` / `queue wait-for`
    orchestration loop, git/PR through the relay, plan-mode approval flow, provider switching
    (docker/e2b/vercel), and a copy-paste cheatsheet.
  - **Ruflo:** when to swarm vs not, the memory→route→work→store loop, key MCP tool categories,
    `/ruflo-status`, and the daemon caveat.
- Write to `…/scratchpad/agentbox-ruflo-tutorial.html`, publish with `Artifact`, share the URL.

---

## Critical files / commands
- AgentBox host state: `C:\Users\JeremyWilliams\.agentbox\` (`config.yaml`, `state.json`,
  `relay.pid`, `docker-prepared.json`)
- Host `/agentbox` skill: `C:\Users\JeremyWilliams\.claude\skills\agentbox\`
- Codex config touched by `agentbox install codex`: `~/.codex/config.toml`
- Ruflo MCP registrations: managed via `claude mcp` (user scope)
- Reuse existing knowledge: the `agentbox-info` skill (host-side CLI reference) and the
  `grok:setup` / `codex:setup` / `gemini:setup` skills — don't hand-roll what they already cover.

## Verification
1. `agentbox prepare` → `docker`, `e2b`, `vercel` all show **prepared**.
2. `agentbox install codex` exit 0; `~/.codex/config.toml` shows the AgentBox plugin enabled;
   `agentbox codex --help` and `agentbox opencode --help` resolve.
3. Smoke box completes the queued prompt and is destroyed cleanly; plan-mode gate observed via
   `agentbox agent get-plan-question`.
4. `claude mcp list` shows **exactly one** ruflo entry (`plugin:ruflo-core:ruflo`), still
   `✔ Connected`; `ruflo doctor --fix` reports healthy.
5. Tutorial Artifact opens, renders in light+dark, and its command snippets match the verified
   commands above.

## Risks / notes
- **Interactive auth** (E2B, Vercel, and any `:setup` that needs login) can't be done from inside
  this session — you'll run those via `! …`. I'll pause and hand you the exact command.
- `npm -g i` steps are expected no-ops (already latest); included only to honor the request.
- Windows host runs agentbox natively via Docker (WSL Ubuntu-24.04 exists but is Stopped and not
  used). tmux lives *inside* the Linux box, not on the host — no host tmux needed.
- No secrets will be written to any committed/backed-up file; provider tokens stay in the
  provider CLIs' own credential stores.
