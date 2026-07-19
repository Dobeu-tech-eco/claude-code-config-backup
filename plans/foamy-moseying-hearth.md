# OMC Setup — Global, Preserve Mode

## Context

You just installed the `oh-my-claudecode` (OMC) plugin (v4.15.4) and invoked `/oh-my-claudecode:omc-setup`. Setup has **never run** on this machine — there is no `~/.claude/.omc-config.json`, so this is a fresh full setup.

Your global config is heavily customized: `~/.claude/CLAUDE.md` holds ~350 lines of Ruflo + Automation-Architect + agent-catalog instructions, plus a large `~/.claude/rules/` tree and a project-level `C:\Users\JeremyWilliams\CLAUDE.md`. OMC's **default** global mode (`overwrite`) would replace `~/.claude/CLAUDE.md` outright. You chose **preserve** mode instead, so that config stays intact.

**What preserve mode actually does** (from the coordinator, `scripts/setup-claude-md.sh` + `phases/01-install-claude-md.md`):
- Writes OMC's canonical instructions to a **new** file `~/.claude/CLAUDE-omc.md` (loaded only when you launch via the `omc` wrapper, not plain `claude`).
- Inserts **exactly one small managed-import block** into your base `~/.claude/CLAUDE.md` — this is the only change to your file, and the coordinator makes a **byte-identical backup** first. Fully reversible.
- The coordinator (`bridge/claude-md-coordinator.cjs`) is the sole writer, with a source-hash handshake and fail-closed rollback. We never hand-edit or download these files.

Outcome: plain `claude` keeps your exact Ruflo setup; `omc` gives you OMC on top.

## Prerequisite check (run first)

`jq` and `node` are required by phases 2–4 (config/settings merges). Verify before proceeding:
```bash
command -v node && command -v jq && command -v npm || echo "MISSING TOOL"
```
If `jq` is missing, the CLAUDE.md install (Phase 1) still works, but the `.omc-config.json` / `settings.json` steps will refuse to run. Install jq or skip those optional steps.

## Phase 1 — Install CLAUDE.md (the core change)

Run the coordinator in preserve mode (do **not** use Write; the script is the only sanctioned path):
```bash
bash "C:/Users/JeremyWilliams/.claude/plugins/cache/omc/oh-my-claudecode/4.15.4/scripts/setup-claude-md.sh" global preserve
```
Then **verify**:
- `~/.claude/CLAUDE-omc.md` exists and contains both OMC markers.
- `~/.claude/CLAUDE.md` contains **exactly one** managed-import block and is otherwise unchanged (diff against the coordinator-reported backup).
- Report the exact backup path the coordinator prints. If the coordinator reports failure/rollback, **stop** and surface it — no fallback edits.

Save progress: `setup-progress.sh save 2 global`.

## Phases 2–4 — Optional configuration (interactive)

These phases mutate `~/.claude/settings.json` and `~/.claude/.omc-config.json` (jq merges that preserve existing keys — your `attribution`/hooks stay intact). **Decisions confirmed** — enable all four extras:

- **2.1 HUD statusline** → ✅ ENABLE. Delegate to `hud` skill (`/oh-my-claudecode:hud setup`). Adds `statusLine` to settings.json; Windows path handling stays inside the skill.
- **2.3 Version check** → informational only.
- **2.4 Default execution mode** → ✅ set `ultrawork`. Writes `defaultExecutionMode: "ultrawork"` to `.omc-config.json`.
- **2.5 OMC CLI** → ✅ INSTALL via `npm install -g oh-my-claude-sisyphus`. Enables `omc hud`, `omc team`, `omc teleport`. If npm perms fail, report and continue (non-blocking).
- **2.6 Task tool** → only prompts if `bd`/`br` detected; else built-in Tasks (no action).
- **3.2 MCP servers** → **skip** — you already have an extensive MCP set; do not re-run mcp-setup.
- **3.3 Agent teams** → ✅ ENABLE. Sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings.json + team defaults (3 agents, provider `claude`, display Auto). Verify settings.json stays valid JSON with your existing keys intact.
- **4 Welcome + star prompt** → informational; marks `.omc-config.json` setupCompleted. GitHub star prompt is optional (skip is fine).

## Verification (end-to-end)

1. `cat ~/.claude/CLAUDE-omc.md | head` shows OMC canonical content with markers.
2. `~/.claude/CLAUDE.md` = original + one managed-import block only (confirm via backup diff).
3. `jq . ~/.claude/settings.json` is valid JSON and still contains your pre-existing keys (hooks, attribution, plugin entries).
4. `~/.claude/.omc-config.json` exists with `setupCompleted` set.
5. Plain `claude` still loads your Ruflo config unchanged; `omc` wrapper loads CLAUDE-omc.md.

## Rollback

If anything looks wrong: restore `~/.claude/CLAUDE.md` from the coordinator-reported backup, delete `~/.claude/CLAUDE-omc.md`, and remove any added settings.json keys. The coordinator auto-rolls-back on its own failures.

## Confirmed decisions

- Global config handling: **preserve** (base `~/.claude/CLAUDE.md` untouched except one managed-import block + backup).
- Extras: **HUD statusline**, **omc CLI (npm -g)**, **agent teams**, and **default mode = ultrawork** — all enabled.
- **MCP servers left alone** — no re-run of mcp-setup; your existing MCP set stays as-is.
