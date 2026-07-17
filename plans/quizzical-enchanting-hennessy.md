# Plan: Mirror Windows `~/.claude` config into WSL (Ubuntu 24.04)

## Context

Claude Code is installed and richly configured on Windows (`C:\Users\JeremyWilliams\.claude`), but the WSL2 Ubuntu 24.04 distro on the same machine (`jeremyw`, `/home/jeremyw`) has **no `~/.claude`, no Claude Code, and no Linux Node** — the `npm` WSL currently sees resolves to the Windows `node.exe` via PATH interop, which cannot host a Linux stdio MCP server. The goal: give the WSL user the same effective configuration as Windows (skills, agents, commands, rules, CLAUDE.md guidance, MCP servers, Composio plugin, hooks, statusline, permissions), while respecting that the two OSes need different machinery.

**Chosen strategy (from clarifying questions):**
- **Sync model:** Windows is the author; WSL is a mirror refreshed by a re-runnable `rsync` script. Each side keeps its own `settings.json`, auth, and session state.
- **Hooks/statusline:** Port the 3 PowerShell hooks + statusline to bash (native speed; statusline runs on every TUI render, so `pwsh` cold-start is unacceptable).
- **Scope:** Also carry MCP servers (+ Linux Node), the Composio plugin/marketplace, a path-translated permissions allowlist, and a WSL-adapted CLAUDE.md.

**What is portable vs. Windows-bound**

| Portable (mirror as-is) | Windows-bound (re-create for Linux) |
|---|---|
| `agents/` (36), `commands/` (18), `skills/` (377 files), `rules/` (9), `system-prompts/`, `tools/`, `prompts/` | `.credentials.json` (machine-local auth) |
| `CLAUDE.md` → adapted variant | `settings.json` / `settings.local.json` (C:/ paths, pwsh hook commands) |
| MCP server *definitions* (memory, sequential-thinking, Context7) | `*.ps1` hooks + `statusline.ps1` |
| Composio marketplace + `enabledPlugins` | `projects/`, `sessions/`, `history.jsonl`, `cache/`, `backups/`, `daemon/`, `shell-snapshots/`, `file-history/`, `jobs/`, `plugins/cache` + `plugins/data` (session/host state) |

## Prerequisites (one-time WSL setup)

Run inside WSL (`wsl.exe -- bash -lc '...'` from Windows, or a WSL shell):

1. **Install jq** (needed by ported hooks): `sudo apt-get update && sudo apt-get install -y jq`
2. **Install Linux Node via nvm** (so `npx` doesn't fall through to Windows `node.exe`):
   ```bash
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
   . ~/.nvm/nvm.sh && nvm install 22 && nvm alias default 22
   ```
   Verify `command -v node` resolves under `~/.nvm/...`, not `/mnt/c/...`.
3. **Install Claude Code** (Windows uses `installMethod: global`): `npm i -g @anthropic-ai/claude-code`
4. **Authenticate separately**: run `claude` once and `/login` (Max-subscription OAuth). Do **not** copy `.credentials.json` from Windows — it is machine/OS-local per the CLAUDE.md Auth policy.

> Note: `G:\` (Google Drive) is **not** mounted in WSL, so a git-repo-on-Drive sync is not possible here; the rsync-from-`/mnt/c` approach is why we chose it.

## Deliverables

### 1. Sync script — `~/.claude/sync-from-windows.sh`
`rsync` the portable subset from `/mnt/c/Users/JeremyWilliams/.claude/` into `~/.claude/`, excluding host/auth/session state and Windows-only scripts. Re-run whenever a skill/agent/command/rule changes on Windows.

Excludes: `.credentials.json`, `settings*.json`, `*.ps1`, `statusline.ps1`, `projects/`, `sessions/`, `history.jsonl`, `cache/`, `backups/`, `daemon/`, `daemon.*`, `shell-snapshots/`, `file-history/`, `jobs/`, `session-env/`, `downloads/`, `plugins/` (Composio is re-fetched natively), `.last-*`, `stats-cache.json`, `mcp-needs-auth-cache.json`, `hooks/*.ps1`, `hooks/legacy-linux-hooks.json.reference`, and the bash artifacts this plan creates (so a sync never clobbers them): `hooks/*.sh`, `sync-from-windows.sh`, `settings*.json`.

Uses `rsync -a --delete` scoped to the included trees. `--delete` keeps removals on Windows propagating to WSL, but the exclude list protects WSL-only files.

### 2. Bash-ported hooks — `~/.claude/hooks/*.sh`
Faithful 1:1 ports of the PowerShell logic (behavior documented in `hooks/README.md`). All three **fail open** (exit 0 on any internal error) and read the hook JSON payload from stdin via `jq`.

- **`pre-commit-secret-scan.sh`** (PreToolUse / `Bash`, **blocking**): fast-exit 0 unless `.tool_input.command` matches `git … commit`. Locate repo with `git -C "$cwd" rev-parse --show-toplevel`; scan staged `--diff-filter=ACMR` files ≤2 MB. Patterns: generic `(api[_-]?key|secret|password|token|private[_-]?key)\s*[:=]\s*["']?[A-Za-z0-9_-]{20,}` (case-insensitive) plus vendor prefixes `ghp_`, `sk-proj-`, `sk-ant-`, `ntn_`, `tvly-`. `exit 1` with file:line findings on a hit; else `exit 0`.
- **`post-edit-format.sh`** (PostToolUse / `Edit|Write`, **never blocks**): only `.ts/.tsx/.js/.jsx`. Run `prettier --write` if on PATH; find nearest `package.json` root, and if `tsconfig.json` exists run `npx --no-install tsc --noEmit --pretty false` bounded by `timeout 60` (present in WSL). Surface only errors mentioning this file's rel-path/basename, plus config-level `TS5xxx/TS6xxx` failures. Always `exit 0`.
- **`post-edit-console-log.sh`** (PostToolUse / `Edit|Write`, **warn only**): only `.ts/.tsx/.js/.jsx` ≤2 MB; warn to stderr with line numbers of `console.log` (cap 10 shown). Always `exit 0`.

The `Invoke-Bounded` process-timeout dance in the PowerShell version becomes GNU `timeout <secs> <cmd>` in bash — simpler and equivalent.

### 3. Bash-ported statusline — `~/.claude/statusline.sh`
Reads status JSON on stdin (via `jq`), prints one line:
`<model_display_name> <output_style> <project>/<relpath> (<branch> +staged ~modified ?untracked) [HH:MM]`
with the same dimmed ANSI colors (cyan model, magenta style, blue path, yellow-dirty/green-clean git, grey time). Path logic: project basename + path relative to `project_dir`; git counts from `git status --porcelain` (`^[MADRC]`=staged, `^.M`=modified, `^??`=untracked). Must **never** write to stderr or fail (fallback prints `Claude`).

### 4. WSL `settings.json` — `~/.claude/settings.json`
Mirror of the Windows file with Linux-appropriate values:
- `model: "opus[1m]"`, `theme: "dark"`, `tui: "fullscreen"`, `autoUpdatesChannel: "latest"`, `skipWorkflowUsageWarning: true`.
- **hooks** point at bash: `bash /home/jeremyw/.claude/hooks/<name>.sh` for the same PreToolUse `Bash` and PostToolUse `Edit|Write` matchers.
- **statusLine**: `bash /home/jeremyw/.claude/statusline.sh`.
- **Composio**: `extraKnownMarketplaces.composio` (github `ComposioHQ/composio-plugin-cc`) + `enabledPlugins."composio@composio": true` — Claude re-installs the plugin natively on first launch.

### 5. WSL `settings.local.json` — path-translated permissions
Copy the allow list, rewriting `Read(C:/Users/JeremyWilliams/**)` → `Read(/home/jeremyw/**)`. The `Bash(...)`, `WebFetch(...)`, and `Bash(claude mcp *)` entries port unchanged.

### 6. MCP servers (re-registered, not file-copied)
After Linux Node is in place, register the three stdio servers at user scope so they run under Linux `npx`:
```bash
claude mcp add-json memory '{"type":"stdio","command":"npx","args":["-y","@modelcontextprotocol/server-memory"],"env":{}}' --scope user
claude mcp add-json sequential-thinking '{"type":"stdio","command":"npx","args":["-y","@modelcontextprotocol/server-sequential-thinking"],"env":{}}' --scope user
claude mcp add-json Context7 '{"type":"stdio","command":"npx","args":["-y","@upstash/context7-mcp"],"env":{}}' --scope user
```
(The `memory` server keeps its own Linux-side graph file — WSL and Windows memory graphs stay independent, which is expected.)

### 7. WSL-adapted `CLAUDE.md`
The Windows CLAUDE.md hard-codes PowerShell, `C:\` paths, `G:\` Drive, and forbids bash-isms — all inverted under WSL. Produce a WSL variant that:
- Sets Environment to Ubuntu 24.04 under WSL2, user `jeremyw`, shell **bash**, repos at `/home/jeremyw/repos`, Windows side readable at `/mnt/c/...`, and **notes `G:\` Drive is not mounted**.
- Replaces the "no bash-isms / use pwsh cmdlets" rule with the reverse (bash is native here).
- **Keeps intact** the portable sections: the Automation Architect tool-routing tree, Composio/Rube/Make orchestration, session/auth/workbench rules (the remote workbench is Linux either way).

## Execution order

1. WSL prereqs: `jq`, nvm+Node 22, `npm i -g @anthropic-ai/claude-code`, `claude`+`/login`.
2. `mkdir -p ~/.claude/hooks ~/.claude/plans`.
3. Write `sync-from-windows.sh`; run it → pulls agents/commands/skills/rules/etc. into `~/.claude`.
4. Write the 4 bash scripts (`hooks/*.sh`, `statusline.sh`); `chmod +x` them.
5. Write `settings.json`, `settings.local.json`, and the WSL `CLAUDE.md`.
6. Register the 3 MCP servers.

## Verification

- **Node origin**: `wsl -- bash -lc 'command -v node && node -v'` → resolves under `~/.nvm`, v22.x (not `/mnt/c/...`).
- **Claude up**: `wsl -- bash -lc 'claude --version'` and `claude mcp list` → all three servers `connected`.
- **Sync fidelity**: `diff -r` (names only) of `agents/`, `commands/`, `rules/` between `/mnt/c/.../.claude` and `~/.claude` → no missing files; `ls ~/.claude/skills | wc -l` matches Windows count.
- **statusline**: `echo '{"model":{"display_name":"Opus"},"workspace":{"current_dir":"/home/jeremyw/repos/x","project_dir":"/home/jeremyw/repos/x"}}' | bash ~/.claude/statusline.sh` → prints a colored single line, no stderr.
- **secret hook blocks**: in a throwaway git repo, stage a file containing `api_key = "AKIA0000000000000000abcd"`, then `echo '{"tool_input":{"command":"git commit -m x"},"cwd":"<repo>"}' | bash ~/.claude/hooks/pre-commit-secret-scan.sh; echo "exit=$?"` → exit 1 + finding. A clean file → exit 0, silent.
- **secret hook fast-path**: payload with `"command":"ls -la"` → exit 0, no output.
- **format hook non-blocking**: feed an `Edit` payload for a `.ts` file with a `console.log` and a type error → warnings on stderr, `exit=0`; a `.md` file payload → exit 0, silent.
- **hooks live in TUI**: start `claude` in WSL, edit a `.ts` file (statusline renders, post-edit warnings appear), attempt a `git commit` of a seeded secret (blocked).
- **CLAUDE.md sanity**: confirm the WSL `CLAUDE.md` no longer instructs pwsh/`C:\`/`G:\` and that Automation-Architect routing survived.

## Non-goals / notes

- Not copying auth, session history, projects, caches, or `plugins/` binaries — those are host-local or re-fetched.
- Windows config is untouched; this is additive to WSL only.
- Re-run `sync-from-windows.sh` after future Windows-side skill/agent edits; the bash hooks, statusline, and WSL settings are excluded from the sync so they persist.
