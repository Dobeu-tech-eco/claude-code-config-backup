# WSL Hardening + Claude Code Config Port — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop WSL from freezing the host, then mirror the Windows Claude Code user configuration into the WSL Ubuntu-24.04 Claude Code install.

**Architecture:** Two strictly ordered stages. Stage A (Tasks 1–3) makes it safe to run WSL at all — the host currently has 1.79 GB free RAM and no `.wslconfig`, so an uncapped WSL2 VM triggers a paging storm and a hard hang. Stage B (Tasks 4–10) ports ~7 MB of genuinely portable config; the Windows tree is 1,030 MB, but 99.3% of that is `plugins/` and `projects/`, which must be rebuilt natively rather than copied. Windows remains the authoring side; WSL is a mirror.

**Tech Stack:** Windows 11 Insider 26340.9233 · WSL 2.9.8.0 / kernel 6.18.40.1-1 · Ubuntu-24.04 (user `jeremyw`, `/home/jeremyw`) · PowerShell 7 host-side · bash + rsync + jq + node/nvm guest-side.

**Spec:** Derived from the 62-finding recon in run `wf_8179a4e4-0ba`. Raw findings: `%TEMP%\claude\C--Users-JeremyWilliams\c1594645-933a-40fd-9e38-cfb5b6880591\scratchpad\recon-findings.json` and `verify-verdicts.json`.

## Global Constraints

- **The Ubuntu-24.04 distro MUST stay `Stopped` until Task 1 and Task 2 are both complete.** It is currently Stopped. Booting it before the caps exist risks the exact freeze being fixed.
- **Never copy into WSL, under any circumstance:** `.credentials.json` (live multi-service OAuth vault), `.claude.json`, `.claude.json.backup`, `backups/`, `daemon/` (contains `control.key`, `pipe.key`), `sessions/` (`*.key`). WSL authenticates independently via its own `/login`.
- **Every rsync exclude must be anchored with a leading `/`** so it matches only the tree root and does not nuke same-named files nested inside `skills/`.
- **Transfer budget is ~7 MB / ~700 files.** If a transfer approaches 1 GB, an exclude is wrong — stop and fix the manifest.
- Windows-side paths: `C:\Users\JeremyWilliams\.claude`. WSL-side: `/home/jeremyw/.claude`. Windows tree reachable from WSL at `/mnt/c/Users/JeremyWilliams/.claude`.
- `G:\` (streamed Google Drive) does **not** exist in WSL and cannot be DrvFs-mounted. Never rewrite `G:\` to `/mnt/g`.
- Driving WSL from the Git-Bash `Bash` tool requires `MSYS_NO_PATHCONV=1`, and inline `$VAR` in `wsl.exe -- bash -lc '...'` expands to empty. Author self-contained script files and invoke them with literal absolute paths only.

---

## File Structure

| Path | Responsibility | Action |
|---|---|---|
| `C:\Users\JeremyWilliams\.wslconfig` | Host-side WSL2 VM resource caps | **Create** |
| `/home/jeremyw/.claude/settings.json` | WSL hooks, statusLine, permissions, enabledPlugins | **Author fresh** (never copy) |
| `/home/jeremyw/.claude/settings.local.json` | WSL permission allowlist | **Author fresh** |
| `/home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh` | bash port of the blocking PowerShell scanner | **Create** |
| `/home/jeremyw/.claude/statusline.sh` | bash port of `statusline.ps1` | **Create** |
| `/home/jeremyw/.claude/hooks/ccg/*.js` | 5 node hooks | **Copy verbatim** (path rewrite in settings only) |
| `/home/jeremyw/.claude/skills/`, `rules/`, `helpers/`, `_archive/`, `system-prompts/`, `docs/`, `.ccg/` | Portable content | **rsync** |
| `/home/jeremyw/.claude/projects/<linux-slug>/memory/` | Canonical file-memory | **Copy to slug-corrected path** |
| `/home/jeremyw/.claude/CLAUDE.md` | Environment instructions | **Author fresh** (Windows prose is actively wrong under Linux) |
| `~/.claude/sync-from-windows.sh` | Repeatable mirror | **Rewrite** from `.gitignore` whitelist |

---

## Task 1: Cap the WSL2 VM before it can boot again

**Files:**
- Create: `C:\Users\JeremyWilliams\.wslconfig`

**Interfaces:**
- Produces: a global cap applying to **every** WSL2 VM on the host — both `Ubuntu-24.04` and `cowork-vm-afa6e102` (Claude Cowork). Later tasks assume ≤6 GB / ≤6 vCPU per VM.

**Why this is Task 1:** With no `.wslconfig`, each WSL2 VM is entitled to 50% of RAM (~15.5 GB), all 16 logical processors, and an 8 GB swap VHD. Two such VMs exist. The host is already at 69.23 GB committed against a 103.12 GB limit with 1.79 GB free physical RAM and a pagefile grown to 72 GB. Three Kernel-Power 41 events on 2026-08-17/18 confirm the hangs; the 22:00:26 one carries BugcheckCode 307 = `0x133 DPC_WATCHDOG_VIOLATION`, the signature of a guest owning every core.

- [ ] **Step 1: Confirm the distro is stopped and no config already exists**

```powershell
wsl --list --verbose
Test-Path C:\Users\JeremyWilliams\.wslconfig
```

Expected: `Ubuntu-24.04  Stopped  2`, and `False`. If the distro is `Running`, run `wsl --shutdown` first and re-check. If the file exists, back it up before overwriting.

- [ ] **Step 2: Write the capped config**

```powershell
@'
# %UserProfile%\.wslconfig  --  C:\Users\JeremyWilliams\.wslconfig
# Host: 31.12 GB RAM / 16 logical CPUs.
# NOTE: every cap below is PER WSL2 VM, and this host runs two
# (Ubuntu-24.04 and cowork-vm-*), so budget for 2x these numbers.

[wsl2]
memory=6GB
processors=6
swap=2GB
swapFile=C:\\Users\\JeremyWilliams\\AppData\\Local\\Temp\\wsl-swap.vhdx
vmIdleTimeout=60000
nestedVirtualization=false
networkingMode=nat
guiApplications=false

[experimental]
autoMemoryReclaim=dropCache
sparseVhd=true
'@ | Set-Content -Path C:\Users\JeremyWilliams\.wslconfig -Encoding utf8
```

Per-setting justification:
- `memory=6GB` — replaces the ~15.5 GB default; two VMs then peak at 12 GB, not ~31 GB.
- `processors=6` — host always retains 10 cores for DPC servicing. Directly targets the `0x133`.
- `swap=2GB` — the host pagefile is already 72 GB; shrink guest swap rather than add host commit charge.
- `swapFile=` — pins the VHD to a findable path instead of the churned `%Temp%\swap.vhdx`.
- `vmIdleTimeout=60000` — states the default explicitly so idle VMs are torn down.
- `nestedVirtualization=false` — drops a hypervisor layer. Set back to `true` **only** if running Docker/KVM inside the distro.
- `networkingMode=nat` — pins the currently-working mode. Do **not** try `mirrored` while chasing a host hang; it adds host-stack involvement.
- `guiApplications=false` — removes WSL from the GPU path on this dual-GPU laptop (nvlddmkm 153 on 08/16, three DWM VRAM-thrashing warnings on 08/19).
- `sparseVhd=true` — applies to **new** VHDs only; the existing one is handled in Step 4.

- [ ] **Step 3: Apply and observe the 8-second rule**

```powershell
wsl --shutdown
Start-Sleep -Seconds 10
Get-Content C:\Users\JeremyWilliams\.wslconfig
```

- [ ] **Step 4: Make the existing VHD sparse (distro must be stopped)**

```powershell
wsl --manage Ubuntu-24.04 --set-sparse true
```

The VHD is 5.01 GB and confirmed non-sparse. This is hygiene only — disk pressure is **ruled out** as a freeze cause (299 GB free of 930 GB). Do not expect it to change the hang behaviour.

**Verification gate:** `.wslconfig` exists with the exact content above; `wsl -l -v` shows `Stopped`. **Do not boot the distro yet — Task 2 first.**

---

## Task 2: Reduce host memory pressure

**Files:** none — this is host state, not config.

**Interfaces:**
- Consumes: the caps from Task 1.
- Produces: enough free RAM that starting a 6 GB VM is survivable.

**Why:** The recon is explicit that `.wslconfig` is *necessary but not sufficient*. With WSL fully stopped, the host still sits at 1.79 GB free physical RAM, 955 processes, **156 `node.exe` instances**, and 2.5 GB in Memory Compression. A capped VM started into that state can still hang the machine.

- [ ] **Step 1: Measure the baseline**

```powershell
$os = Get-CimInstance Win32_OperatingSystem
"FreePhysicalGB : {0:N2}" -f ($os.FreePhysicalMemory/1MB)
"CommittedGB    : {0:N2}" -f ((Get-Counter '\Memory\Committed Bytes').CounterSamples[0].CookedValue/1GB)
"CommitLimitGB  : {0:N2}" -f ((Get-Counter '\Memory\Commit Limit').CounterSamples[0].CookedValue/1GB)
"Processes      : " + (Get-Process).Count
"node.exe       : " + (Get-Process node -ErrorAction SilentlyContinue).Count
```

- [ ] **Step 2: Identify what is holding memory**

```powershell
Get-Process node -ErrorAction SilentlyContinue |
  Sort-Object WorkingSet -Descending |
  Select-Object -First 20 Id, @{n='WS_MB';e={[math]::Round($_.WorkingSet/1MB)}}, StartTime, Path |
  Format-Table -AutoSize
```

- [ ] **Step 3: Decide with the user, then reclaim**

**Do not mass-kill processes autonomously** — some `node.exe` instances are live MCP servers and plugin daemons belonging to running Claude Code sessions. Present the Step 2 table and confirm which are stale before terminating anything. The safe reclaim actions, in order of preference:

1. Close Claude Code sessions that are no longer in use (each carries its own MCP server set).
2. Stop the Claude Cowork VM if it is not in use — `vmmem` PID has been resident since 13:21 holding 4.1 GB.
3. Reboot the host. This is the cleanest single action given a 72 GB pagefile and 20 days of accumulated state.

- [ ] **Step 4: Re-measure and gate**

Re-run Step 1. **Gate: proceed only when FreePhysicalGB ≥ 8.** If it is still under 8 GB, do not boot WSL — return to Step 3.

---

## Task 3: Controlled first boot with live monitoring

**Files:** none.

**Interfaces:**
- Consumes: Task 1 caps, Task 2 headroom.
- Produces: a verified-safe running distro; all later tasks run inside it.

- [ ] **Step 1: Arm host-side monitoring before booting**

Open a second PowerShell window and leave this running:

```powershell
while ($true) {
  $c = (Get-Counter '\Memory\Committed Bytes').CounterSamples[0].CookedValue/1GB
  $f = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB
  $v = (Get-Process vmmem,vmmemWSL -ErrorAction SilentlyContinue |
        Measure-Object WorkingSet -Sum).Sum/1GB
  "{0}  commit={1:N1}GB  free={2:N1}GB  vmmem={3:N1}GB" -f (Get-Date -f HH:mm:ss), $c, $f, $v
  Start-Sleep 3
}
```

- [ ] **Step 2: Boot the distro**

```powershell
wsl -d Ubuntu-24.04 -- echo "wsl-up"
```

Expected: `wsl-up`.

- [ ] **Step 3: Watch for 60 seconds and confirm the cap holds**

Success criteria, read off the monitor from Step 1:
- `vmmem` stabilises **at or below ~6 GB** — this proves `.wslconfig` is being read.
- `free` does **not** trend toward zero.
- `commit` does not climb toward the 103 GB limit.

If `vmmem` exceeds 6 GB, `.wslconfig` was not applied — `wsl --shutdown`, re-check the file path and encoding, and repeat.

- [ ] **Step 4: Confirm the guest sees the caps**

```powershell
wsl -d Ubuntu-24.04 -- bash -lc "free -h; nproc"
```

Expected: total memory ≈ 6 GB (not ~15 GB), `nproc` = 6 (not 16).

**Rollback if the host hangs again:** power-cycle, then from an elevated prompt `wsl --shutdown`. If WSL will not stop cleanly, `wsl --terminate Ubuntu-24.04`. `wsl --unregister Ubuntu-24.04` is a **last resort — it destroys the distro and all data in it**, including any prior mirror; take a `wsl --export` backup first.

**Note on diagnostics:** crash dumps are currently broken — BitLocker logs error 24641 ("could not retrieve volume master key during restart") two seconds before each hang, and `volmgr` 161 reports dump creation failed with `BugCheckProgress 0x00000081`. `C:\Windows\MEMORY.DMP` and `C:\Windows\Minidump\` are both empty. **Validate the fix by prevention (live monitoring), not by post-mortem.** Fixing dump collection is out of scope for this plan.

---

## Task 4: Verify and establish the WSL runtime baseline

**Files:**
- Verify/Create in WSL: node via nvm, `@anthropic-ai/claude-code`, `jq`, `git`, `rsync`

**Interfaces:**
- Produces: `claude`, `node`, `npx`, `jq`, `git`, `rsync` on PATH inside the distro. Every later task depends on these. `jq` in particular is required by every bash hook.

A prior mirror was made 2026-07-14, but it is six weeks stale and unverified. Verify rather than assume.

- [ ] **Step 1: Author a self-contained probe script**

Write to the scratchpad (avoids the inline-variable-eating trap):

```bash
#!/usr/bin/env bash
export HOME=/home/jeremyw
. "$HOME/.nvm/nvm.sh" 2>/dev/null || true
echo "node:   $(command -v node || echo MISSING) $(node -v 2>/dev/null)"
echo "npm:    $(command -v npm || echo MISSING) $(npm -v 2>/dev/null)"
echo "claude: $(command -v claude || echo MISSING) $(claude --version 2>/dev/null)"
echo "jq:     $(command -v jq || echo MISSING)"
echo "git:    $(command -v git || echo MISSING)"
echo "rsync:  $(command -v rsync || echo MISSING)"
echo "--- existing config ---"
ls -la "$HOME/.claude" 2>/dev/null | head -40 || echo "no ~/.claude"
echo "--- projects slugs ---"
ls "$HOME/.claude/projects" 2>/dev/null || echo "none"
```

- [ ] **Step 2: Run it (note the CRLF strip and literal paths)**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "sed 's/\r$//' /mnt/c/Users/JeremyWilliams/AppData/Local/Temp/claude/probe.sh > /tmp/probe.sh && bash /tmp/probe.sh"
```

- [ ] **Step 3: Install whatever is MISSING**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "sudo apt-get update && sudo apt-get install -y jq rsync git"
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "source ~/.nvm/nvm.sh && npm install -g @anthropic-ai/claude-code"
```

`apt-get` will prompt for a sudo password — this step is interactive.

- [ ] **Step 4: Re-run the probe and confirm zero MISSING**

---

## Task 5: Build the transfer manifest and rsync the portable tree

**Files:**
- Create: `/home/jeremyw/.claude/sync-from-windows.sh`
- Source of truth: `C:\Users\JeremyWilliams\.claude\.gitignore`

**Interfaces:**
- Consumes: Task 4's `rsync`.
- Produces: `skills/`, `rules/`, `hooks/ccg/`, `helpers/`, `_archive/`, `system-prompts/`, `docs/`, `.ccg/`, `mcp-scaffold.json` present in `/home/jeremyw/.claude/`.

**Key insight:** the `.claude` tree is already a git repo whose `.gitignore` encodes exactly the MIRROR-vs-exclude split, written with the secret/volatility distinction in mind. Reuse it as the manifest rather than inventing a second, divergent deny-list.

**Port arithmetic:** excluding `plugins/` (838.73 MB / 55,591 files, full of `win32-x64` native binaries) and `projects/` (167.13 MB of session transcripts) reduces the transfer from ~1,030 MB to **~7 MB / ~700 files — a 99.3% reduction.**

- [ ] **Step 1: Read the existing exclude list before trusting it**

The prior `sync-from-windows.sh` cannot be verified from the Windows side. Print it from inside WSL:

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "cat /home/jeremyw/.claude/sync-from-windows.sh 2>/dev/null || echo 'ABSENT'"
```

Confirm it carries **anchored** excludes for at least `.credentials.json`, `/projects/`, `/plugins/`, `/backups/`, `/daemon/`, `/sessions/`. If any are missing, do not run it — replace it in Step 2.

- [ ] **Step 2: Write the new sync script**

```bash
#!/usr/bin/env bash
set -euo pipefail
SRC=/mnt/c/Users/JeremyWilliams/.claude/
DST=/home/jeremyw/.claude/

rsync -av --delete-excluded \
  --exclude='/.credentials.json' \
  --exclude='/.claude.json' \
  --exclude='/.claude.json.backup' \
  --exclude='/backups/' \
  --exclude='/daemon/' \
  --exclude='/sessions/' \
  --exclude='/session-env/' \
  --exclude='/session-data/' \
  --exclude='/shell-snapshots/' \
  --exclude='/tasks/' --exclude='/teams/' --exclude='/jobs/' \
  --exclude='/file-history/' --exclude='/cache/' --exclude='/paste-cache/' \
  --exclude='/metrics/' --exclude='/ide/' --exclude='/downloads/' --exclude='/prompts/' \
  --exclude='/plugins/' \
  --exclude='/projects/' \
  --exclude='/bin/' \
  --exclude='/tools/' \
  --exclude='/.git/' \
  --exclude='/settings.json' \
  --exclude='/settings.local.json' \
  --exclude='/CLAUDE.md' \
  --exclude='/CLAUDE-omc.md' \
  --exclude='/statusline.ps1' \
  --exclude='/ai-stack-sync/backups/' \
  --exclude='*.log' \
  --exclude='/history.jsonl' \
  --exclude='/.session-stats.json*' \
  --exclude='/daemon.lock' \
  --exclude='/daemon.status.json' \
  --exclude='*.bak-*' \
  --exclude='*.backup.*' \
  "$SRC" "$DST"
```

Every exclude is anchored with a leading `/` except the three glob patterns, which are intentionally unanchored. `settings.json`, `settings.local.json`, `CLAUDE.md`, and `CLAUDE-omc.md` are excluded because they are **authored fresh** in Tasks 6 and 9 — copying them would import PowerShell hook commands that break every Bash call.

- [ ] **Step 3: Dry-run first and check the byte count**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "sed 's/\r$//' /mnt/c/Users/JeremyWilliams/AppData/Local/Temp/claude/sync.sh > /tmp/sync.sh && bash -c 'bash /tmp/sync.sh --dry-run' 2>&1 | tail -20"
```

Add `--dry-run` to the rsync line for this step. **Gate: total transferred size must be under ~20 MB.** If it reports hundreds of MB, an exclude is wrong — fix before proceeding.

- [ ] **Step 4: Run for real, in batches**

Given the freeze history, transfer in stages rather than one sweep — run with `--exclude='/_archive/'` first, confirm the host monitor stays flat, then re-run without it.

- [ ] **Step 5: Verify content landed**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "du -sh /home/jeremyw/.claude; ls /home/jeremyw/.claude; find /home/jeremyw/.claude/skills -type f | wc -l"
```

Expected: ~7 MB total, `skills/` present with ~276 files.

**Note:** `agents/` and `commands/` are **empty** on the Windows side despite what `CLAUDE.md` claims. Create them as empty directories for structural parity; do not report them as ported content.

---

## Task 6: Author the WSL settings.json

**Files:**
- Create: `/home/jeremyw/.claude/settings.json`
- Reference: `C:\Users\JeremyWilliams\.claude\hooks\legacy-linux-hooks.json.reference`

**Interfaces:**
- Consumes: `hooks/ccg/*.js` from Task 5; `jq` from Task 4.
- Produces: a settings file whose every hook command resolves under Linux.

**Why authored, not copied:** `settings.json` is the single most Windows-bound file in the tree. Two hooks are `critical` breakages — the `PreToolUse` secret scanner is a **blocking** hook on matcher `Bash`, so under Linux it fails to spawn on *every single Bash tool call*.

A ready-made bash hooks block already exists in the tree at `hooks/legacy-linux-hooks.json.reference` (9,897 bytes) — the Linux ancestor of the current PowerShell hooks, using the same secret-scan regexes. Use it as the base, but note it **predates the ccg node hooks**, which must be added.

- [ ] **Step 1: Rewrite the four node hook paths**

The JS itself is portable — `skill-router.js` already prefers `process.env.HOME` over `USERPROFILE`. This is a pure path rewrite:

| JSON pointer | New command |
|---|---|
| `hooks.PreToolUse[1].hooks[0].command` | `node /home/jeremyw/.claude/hooks/ccg/subagent-context.js` |
| `hooks.UserPromptSubmit[0].hooks[0].command` | `node /home/jeremyw/.claude/hooks/ccg/workflow-state.js` |
| `hooks.UserPromptSubmit[0].hooks[1].command` | `node /home/jeremyw/.claude/hooks/ccg/skill-router.js` |
| `hooks.SessionStart[0].hooks[0].command` | `node /home/jeremyw/.claude/hooks/ccg/session-start.js` |

Preserve the existing `matcher` and `timeout` values verbatim.

- [ ] **Step 2: Replace the two PowerShell entries**

- `hooks.PreToolUse[0].hooks[0].command` → `bash /home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh` (built in Task 7)
- `statusLine.command` → `bash /home/jeremyw/.claude/statusline.sh` (built in Task 7)

- [ ] **Step 3: Fix the permissions block**

- **Delete** `permissions.allow[6]` — the `PowerShell(...)` tool prefix does not exist on Linux, and the `set_title.ps1` script has no Linux counterpart.
- **Rewrite** `permissions.allow[7]` from `PowerShell(npx @claude-flow/cli@latest hooks worker dispatch --trigger audit)` to `Bash(npx @claude-flow/cli@latest hooks worker dispatch --trigger audit)` — otherwise it silently stops matching and starts prompting.
- **Drop** `permissions.allow[4]` (`Bash(*codeagent-wrapper*)`) unless a Linux build is installed.

- [ ] **Step 4: Fix marketplaces and plugins**

- **Drop** `extraKnownMarketplaces.gitkraken` — it is the only `directory`-source marketplace of 15, pinned to a `C:\` path. The other 14 are `github`/`git` sources and re-clone cleanly.
- **Set** `enabledPlugins["gitkraken-hooks@gitkraken"] = false` — the plugin's `hooks.json` embeds `gk-alpha.exe` ten times.
- **Keep** the rest of `enabledPlugins` (150 entries) and the 14 git-sourced marketplaces verbatim.

- [ ] **Step 5: Port the env block verbatim**

The `env` block (6 vars, no paths) is portable as-is. Ensure `BRIGHTDATA_MCP_TOKEN` is exported in the WSL shell profile — do **not** copy Windows env-var *values* into a WSL `.env`, which would create a second copy of secrets that currently exist in exactly one place.

- [ ] **Step 6: Validate the JSON**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "jq empty /home/jeremyw/.claude/settings.json && jq -r '.hooks | to_entries[] | .value[].hooks[].command' /home/jeremyw/.claude/settings.json"
```

Expected: no parse error, and **zero** output lines containing `pwsh`, `powershell`, or `C:/`.

---

## Task 7: Port the two shell scripts

**Files:**
- Create: `/home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh`
- Create: `/home/jeremyw/.claude/statusline.sh`

**Interfaces:**
- Consumes: `jq` (Task 4).
- Produces: the two executables referenced by Task 6 Step 2.

- [ ] **Step 1: Port the secret scanner**

Take the `PreToolUse` "git commit" entry out of `hooks/legacy-linux-hooks.json.reference` — it already implements this in bash with the same patterns. Port the five vendor prefixes (`ghp_`, `sk-proj-`, `sk-ant-`, `ntn_`, `tvly-`) plus the generic `api[_-]?key|secret|password|token|private[_-]?key` assignment regex using `grep -E`.

**Preserve the fail-open contract:** the PowerShell original exits 0 on internal error. A blocking `PreToolUse` hook that fails closed would break every Bash call.

- [ ] **Step 2: Test it in isolation, both directions**

```bash
echo '{"tool_input":{"command":"echo ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}}' | bash /home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh; echo "exit=$?"
echo '{"tool_input":{"command":"ls -la"}}' | bash /home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh; echo "exit=$?"
```

Expected: the first flags the secret; the second exits 0 silently. **Both must be tested** — a scanner that blocks everything is as broken as one that blocks nothing.

- [ ] **Step 3: Port the statusline**

`statusline.ps1` declares `#Requires -Version 7.0` and uses .NET APIs (`[System.IO.Path]::GetRelativePath`, `[Console]::In`) — not portable even with pwsh installed. Its own header says it is a port **of** `statusline-developer.sh`, so a shell original exists; prefer recovering that, or reuse `helpers/statusline.js`.

Read stdin JSON with `jq`: `.model.display_name`, `.output_style.name`, `.workspace.current_dir`, `.workspace.project_dir`; then `git rev-parse` / `symbolic-ref` / `status --porcelain`. Keep the same ANSI codes.

- [ ] **Step 4: Test the statusline**

```bash
echo '{"model":{"display_name":"Opus 5"},"output_style":{"name":"Proactive"},"workspace":{"current_dir":"/home/jeremyw","project_dir":"/home/jeremyw"}}' | bash /home/jeremyw/.claude/statusline.sh
```

Expected: a single formatted line, no errors.

- [ ] **Step 5: Make both executable**

```bash
chmod +x /home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh /home/jeremyw/.claude/statusline.sh
```

**Do not port** `hooks/post-edit-console-log.ps1` or `hooks/post-edit-format.ps1` — both are referenced by **no** hook in `settings.json` and are already dead on Windows. If that behaviour is wanted, the reference file has bash `PostToolUse` entries for prettier and console.log.

`hooks/backup-commit.ps1` is invoked by Task Scheduler, not `settings.json`, so it will not appear in a settings-only audit. If the WSL side should self-backup, port it to `backup-commit.sh` with `repo=/home/jeremyw/.claude` and wire it to cron or `systemd --user`.

---

## Task 8: Place the memory store at the correct Linux slug

**Files:**
- Create: `/home/jeremyw/.claude/projects/<linux-slug>/memory/`

**Interfaces:**
- Consumes: a running WSL Claude Code (Task 4).
- Produces: the 7 memory files readable by the WSL session.

**Why this needs its own task:** the native file-memory store — the documented "system of record" — is keyed by a **slugified working directory**. Windows uses `C--Users-JeremyWilliams`. Under WSL the cwd is `/home/jeremyw`, so the slug differs. Copied to the Windows-named directory, all 7 memory files are silently never read. This is the single most likely thing to half-work and be mistaken for success.

- [ ] **Step 1: Discover the actual slug empirically — do not guess**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "cd /home/jeremyw && claude -p 'reply with the single word ok' >/dev/null 2>&1; ls /home/jeremyw/.claude/projects/"
```

Whatever directory appears is the correct slug.

- [ ] **Step 2: Copy the memory tree into it**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "SLUG=\$(ls /home/jeremyw/.claude/projects/ | head -1); mkdir -p \"/home/jeremyw/.claude/projects/\$SLUG/memory\"; cp /mnt/c/Users/JeremyWilliams/.claude/projects/C--Users-JeremyWilliams/memory/*.md \"/home/jeremyw/.claude/projects/\$SLUG/memory/\"; ls -la \"/home/jeremyw/.claude/projects/\$SLUG/memory/\""
```

Expected 7 files: `MEMORY.md` plus `agentbox-ruflo-windows-setup.md`, `ccg-multi-model-local-setup.md`, `claude-config-restore-2026-07.md`, `claude-flow-v3-core-repo.md`, `omc-setup-preserve-2026-07.md`, `wsl-claude-config-mirror.md`.

- [ ] **Step 3: Correct the facts, which are now wrong in WSL**

Several memory files assert Windows paths as ground truth. At minimum, rewrite `wsl-claude-config-mirror.md` to describe the new sync script and the corrected slug, and add a note to `claude-config-restore-2026-07.md` that its paths are Windows-side.

- [ ] **Step 4: Verify the memory is actually loaded**

Start a WSL Claude session in `/home/jeremyw` and confirm the `MEMORY.md` index appears in context. If it does not, the slug is wrong — return to Step 1.

---

## Task 9: Author the WSL CLAUDE.md and re-register MCP servers

**Files:**
- Create: `/home/jeremyw/.claude/CLAUDE.md`
- Reference: `C:\Users\JeremyWilliams\.claude\mcp-scaffold.json`

**Interfaces:**
- Produces: correct environment instructions and 3 working MCP servers.

- [ ] **Step 1: Author CLAUDE.md — invert, don't copy**

The Windows `CLAUDE.md` would **actively mis-instruct** a Linux session. Its shell-syntax section forbids `realpath`, `jq`, `$(pwd)`, `/dev/null`, `2>/dev/null` and mandates PowerShell cmdlets — exactly backwards in WSL. Required changes:

- Machine → `WSL2 Ubuntu-24.04`, user `jeremyw`, home `/home/jeremyw`
- Shell → bash; **invert** the entire "Windows shell notes" block so POSIX idioms are mandated
- Repos → `/home/jeremyw/repos` (native ext4 strongly preferred over `/mnt/c` for performance)
- **Delete** every `G:\My Drive` backup instruction — no WSL equivalent exists. Replace with a git-remote push, or word it as an explicitly Windows-side step.
- Correct the Directory Structure section: `agents/` and `commands/` are empty, `todos/` does not exist.

- [ ] **Step 2: Re-register the three portable MCP servers**

Use `mcp-scaffold.json` — the documented, secret-free blueprint. **Omit GitKraken**: it hardcodes `C:\Users\...\GitKrakenCLI\gk-alpha.exe`.

```bash
claude mcp add-json sequential-thinking '{"type":"stdio","command":"npx","args":["-y","@modelcontextprotocol/server-sequential-thinking"]}' --scope user
claude mcp add-json Context7 '{"type":"stdio","command":"npx","args":["-y","@upstash/context7-mcp"]}' --scope user
claude mcp add-json chrome-devtools '{"type":"stdio","command":"npx","args":["chrome-devtools-mcp@latest"]}' --scope user
```

- [ ] **Step 3: Verify**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "claude mcp list"
```

Expected: three servers, all Connected.

- [ ] **Step 4: Do NOT port ccg-skill-routing.md as-is**

`rules/ccg-skill-routing.md` contains 41 absolute paths to `skills/ccg/domains/` — a directory that **does not exist even on Windows today**. The rule is already dead and costs tokens every session. Either drop it from the WSL rules set, or reinstall `ccg-workflow` inside WSL and regenerate it. **Fix this on the Windows side too** — it is a live bug there.

---

## Task 10: Interactive completion — the un-automatable steps

**Files:** none.

**Interfaces:** consumes everything above.

These require a human and cannot be scripted. Budget them explicitly.

- [ ] **Step 1: Authenticate**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "cd /home/jeremyw && claude"
```

Then `/login` for Max-subscription OAuth. **`.credentials.json` is never copied** — WSL auth is independent.

- [ ] **Step 2: Let plugins reinstall**

Claude Code re-clones the 14 git-sourced marketplaces and reinstalls from the `enabledPlugins` map. This re-fetches `linux-x64` optional deps (`@esbuild/linux-x64`, `@img/sharp-linux-x64`, `@ast-grep/napi-linux-x64-gnu`, `@rollup/rollup-linux-x64-gnu`) instead of the `win32-x64` ones. Expect this to take several minutes and pull a few hundred MB.

- [ ] **Step 3: Re-authorize connectors**

44 `claude.ai` connectors are OAuth-side, with no `command`/`args` to rewrite. They must be reconnected interactively. The full list is in `.claude.json` → `claudeAiMcpEverConnected`; print it first so none are missed. Reconnect only the ones actually needed in WSL.

- [ ] **Step 4: Final verification**

- [ ] `claude mcp list` → 3 stdio servers Connected
- [ ] Run a trivial Bash tool call → the `PreToolUse` secret hook does **not** error
- [ ] Statusline renders
- [ ] `MEMORY.md` loads in a session started at `/home/jeremyw`
- [ ] Host monitor: `vmmem` ≤ 6 GB, free RAM stable
- [ ] No `pwsh` / `C:/` in `jq -r '..|.command?//empty' ~/.claude/settings.json`

---

## Open Decisions

Raise these with the user rather than deciding unilaterally:

1. **`_archive/`** (1.52 MB, 130 files) — the only place the deduped agents exist. Copy as insurance (default), or use the port to promote a curated subset back into `agents/`?
2. **`ai-stack-sync/`** — should it become the mechanism that keeps Windows and WSL in sync going forward, rather than a one-shot rsync?
3. **`repos/`** — clone natively into `/home/jeremyw/repos` (fast) or reach the Windows repos via `/mnt/c` (slow, but single source of truth)?
4. **`chrome/chrome-native-host.bat`** — Claude-in-Chrome from WSL needs the native host registered Windows-side and reached over localhost. Non-trivial; excluded by default.
5. **Cowork VM** — should it stay resident? It holds ~4 GB of commit continuously.
6. **Insider Preview** — if freezes recur *after* the caps are in place, moving off the Insider channel becomes the next suspect (a feature update already failed on 08/17 with `0x8024200D`).

---

## Self-Review

**Spec coverage.** All four recon lanes are represented: freeze → Tasks 1–3; inventory → Task 5; portability → Tasks 6, 7, 9; secrets → Global Constraints + Task 5 Step 2. The one recon lane deliverable *not* obtained was the completeness critic (its agents stalled); its role is served by the Open Decisions section and the explicit rollback/verification gates, which I wrote by hand.

**Ordering.** The single hardest constraint — never boot the distro before the caps exist — is stated in Global Constraints and enforced by gates at the end of Tasks 1, 2, and 3.

**Known gap.** Task 7 Step 3 depends on recovering `statusline-developer.sh`, which has not been located. If it cannot be found, the fallback is a fresh `jq`-based port; the `.ps1` remains readable as the behavioural reference. Flagged rather than papered over.

**Not verified.** The WSL-side state (Task 4) is asserted from a six-week-old memory note, not inspection — the distro was deliberately left stopped. Task 4 verifies rather than assumes.
