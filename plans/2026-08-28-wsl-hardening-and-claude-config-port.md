# Host Freeze Remediation + Claude Code Config Port — Implementation Plan

> **REWRITTEN 2026-08-29 00:35.** The original premise — that an uncapped WSL2 VM was exhausting host memory — was **falsified by evidence**. Superseded copy: `2026-08-28-wsl-hardening-and-claude-config-port.SUPERSEDED-wsl-memory-premise.md`. Read "What Changed and Why" below before executing anything.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the recurring whole-host freezes by treating them as the driver-level DPC fault the evidence actually shows, instrument the machine so the next freeze is explainable without a crash dump, then port the portable Windows Claude Code and Codex configuration into WSL Ubuntu-24.04.

**Architecture:** Two stages. Stage A (Tasks 1–5) addresses the freeze: the confirmed signature is `0x133 DPC_WATCHDOG_VIOLATION`, not memory exhaustion, so the work is instrumentation plus a driver update, not resource caps. Stage B (Tasks 6–16) ports Claude Code and Codex declaratively: portable instructions, agents, skills, rules, and OS-neutral settings cross the boundary; plugin caches, native binaries, OAuth/auth files, SQLite/session state, browser/CUA state, project history, and trusted-hook hashes are rebuilt natively rather than copied.

**Tech Stack:** Windows 11 Insider 26340.9233 · PowerShell 7 · `logman`/`schtasks` for instrumentation · WSL 2.9.8.0 / kernel 6.18.40.1-1 · Ubuntu-24.04 (user `jeremyw`, `/home/jeremyw`) · bash + rsync + jq + node/nvm guest-side.

**Spec:** `<workspace>/spec/recon-findings.json` (62 config findings, run `wf_8179a4e4-0ba`) and the freeze root-cause determination from run `wf_397ebfe5-97b` (4 hypotheses, each adversarially cross-examined, plus synthesis). Workspace: `~/.claude/.superpowers/sdd/2026-08-28-wsl-hardening-and-claude-config-port/`.

---

## What Changed and Why

The original plan's Tasks 1–3 were built on a diagnosis that the evidence does not support. Six specific errors, all corrected here:

| Original claim | Reality |
|---|---|
| Kernel-Power 41 shows `BugcheckCode 0` — a pure hang, no crash | **False.** It is **307 = `0x133 DPC_WATCHDOG_VIOLATION`**. The original reading took the event's properties *positionally* instead of by name. This was the load-bearing error. |
| An uncapped WSL2 Ubuntu VM exhausted host memory | The Ubuntu distro **never ran** during either freeze. |
| `.wslconfig` caps brought memory under control | **`.wslconfig` does not govern the Cowork VM at all.** `cowork-vm-afa6e102` is created directly through the Host Compute Service by `cowork-svc.exe`; it is not Lxss-registered and not VMMS-managed. Task 1's caps were a **no-op** for the only VM that was running. |
| Zero compute-system creates 23:00–23:47 ⇒ no VM was running | Invalid inference. The Cowork VM had been alive **since 13:21:54** — ten hours, and through Freeze #1. |
| BitLocker error 24641 blocks the crash-dump write | **Wrong.** `ProtectionStatus = Off` (clear key present), and 24641 fires on ordinary freeze-free boots too. Dumps fail because `BugCheckProgress = 0x00000081` — the dump path aborted before it could run. |
| The 23:46:26 BitLocker/volmgr errors preceded the freeze | Those are **boot-time** records. The true freeze time is **23:42:16** (from EventLog 6008). |

**The evidence that stands.** A two-stage signature repeating identically 11 days apart:

```
08/17  21:59:22  0x133 DPC_WATCHDOG_VIOLATION   then  23:29:45 hang,  00:01:45 hang
08/28  23:42:16  0x133 DPC_WATCHDOG_VIOLATION   then  23:48:46 hang
```

`volmgr 161` ("dump creation failed") appears at **exactly those two `0x133` events and nowhere else in 14 days** — proof a bugcheck was genuinely attempted. Freeze #2 hit **140 seconds after a clean boot**, which arithmetically excludes every accumulation mechanism: commit climbs ~2.5 GB/min on this host, and reaching the 103 GB limit in 140 s would need ~44 GB/min.

**Prime suspect:** the **AMD Radeon 860M** display driver, `32.0.13050.18` dated **2025-04-14** — 16 months old under a 2026 Insider kernel, and the iGPU is in the DPC path. The NVIDIA driver is current (2026-07-21). The AMD stack has **no fault-telemetry provider installed**, so "no AMD errors in the logs" is a blind spot, not an alibi.

**Honest limit:** all four bugcheck parameters came back `0x0` from EFI and no dump exists, so **the specific offending driver cannot be named from logs** — not now, and not on the next occurrence either. Confidence in the driver lane is **medium**. This is why Stage A leads with a cheap reversible driver update plus instrumentation, rather than waiting for an identification that may never arrive.

## Global Constraints

- **Do not power-cycle to "clean things up."** On **both** incident nights the second freeze came after a restart (08/28: restart 23:46:26 → freeze 23:48:46, 140 s). Restarting is the one action with a demonstrated association with a follow-on hang.
- **Do not run Driver Verifier.** Its only output is a bugcheck, which this machine cannot write. It converts a diagnosable hang into an undiagnosable boot loop.
- **Do not buy RAM, and do not suspend BitLocker to "unblock dumps."** The memory lane is refuted for Freeze #2; BitLocker protection is already off and dumps still fail.
- **Do not switch `networkingMode` to `mirrored`**, and do not reinstall/toggle Hyper-V features — the virtualization stack is verified healthy.
- Never copy into WSL: `.credentials.json`, `.claude.json`, `.claude.json.backup`, `backups/`, `daemon/` (holds `control.key`, `pipe.key`), `sessions/` (`*.key`). WSL authenticates independently via its own `/login`.
- **Every rsync exclude must be anchored with a leading `/`** so it matches only the tree root, not same-named files nested inside `skills/`.
- **Transfer budget ~7 MB / ~700 files.** If a transfer approaches 1 GB, an exclude is wrong — stop and fix the manifest.
- `G:\` (streamed Google Drive) does not exist in WSL and cannot be DrvFs-mounted. Never rewrite `G:\` to `/mnt/g`.
- Driving WSL from the Git-Bash `Bash` tool requires `MSYS_NO_PATHCONV=1`; inline `$VAR` inside `wsl.exe -- bash -lc '...'` expands to empty. Author self-contained script files, invoke with literal absolute paths.
- Host paths: `C:\Users\JeremyWilliams\.claude`. WSL: `/home/jeremyw/.claude`. Windows tree visible from WSL at `/mnt/c/Users/JeremyWilliams/.claude`.

---

## File Structure

| Path | Responsibility | Action |
|---|---|---|
| `C:\Users\JeremyWilliams\.wslconfig` | WSL2 VM caps | **Done** (Task 1) — retained, but not the fix |
| `C:\PerfLogs\FreezeWatch*.csv` | 1-second counter log surviving a hard power cut | **Create** (Task 2) |
| Scheduled task `FreezeWatchBoot` | Restarts the collector at boot | **Create** (Task 2) |
| AMD Radeon 860M display driver | The DPC-path suspect | **Update** (Task 4) |
| `/home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh` | bash port of the blocking PowerShell hook | **Create** (Task 9) |
| `/home/jeremyw/.claude/statusline.sh` | bash port of `statusline.ps1` | **Create** (Task 9) |
| `/home/jeremyw/.claude/settings.json` | WSL hooks, statusLine, permissions, plugins | **Author fresh** (Task 10) |
| `/home/jeremyw/.claude/projects/<linux-slug>/memory/` | Canonical file-memory | **Copy to slug-corrected path** (Task 11) |
| `/home/jeremyw/.claude/CLAUDE.md` | Environment instructions | **Author fresh** (Task 12) |
| `~/.claude/sync-from-windows.sh` | Repeatable mirror | **Rewrite** (Task 8) |
| `/home/jeremyw/.codex/config.toml` | Linux-native Codex declarative configuration | **Translate** (Task 15) |
| `/home/jeremyw/.codex/AGENTS.md` | Linux-native global Codex instructions | **Author/translate** (Task 15) |
| `/home/jeremyw/.codex/sync-from-windows.sh` | Repeatable portable Codex mirror | **Create** (Task 15) |

---

# STAGE A — Stop the freezes

## Task 1: WSL2 resource caps — ✅ COMPLETE

**Status:** Done 2026-08-28 23:13:32. Review clean after one fix round; one item parked.

**Artifact:** `C:\Users\JeremyWilliams\.wslconfig` — `memory=6GB`, `processors=4`, `swap=2GB`, `swapFile` outside `%Temp%`, `vmIdleTimeout=60000`, `nestedVirtualization=false`, `networkingMode=nat`, `guiApplications=false`, `autoMemoryReclaim=dropcache`, `sparseVhd=true`. No BOM, LF-normalised.

**Retained deliberately, with its role corrected.** These caps did **not** cause the freezes to stop and were a **no-op for the VM that was actually running** (Cowork is HCS-created and ignores `.wslconfig`). They are kept because they close a real exposure for Stage B: when Ubuntu-24.04 *is* booted in Task 6, it would otherwise be entitled to ~15.5 GB and all 16 cores. Do not treat this task as freeze remediation.

**Parked (Ruling G):** `sparseVhd=true` remains in the file while the platform reports sparse VHD support disabled for data-corruption risk (`wsl --manage --set-sparse` failed with `Wsl/Service/E_INVALIDARG`). Inert today; remove it when `processors` is relaxed back to 6 after a clean week — one edit, not two.

---

## Task 2: Install the FreezeWatch counter log

**Status:** ✅ COMPLETE. `FreezeWatch` is running at a 1-second interval, writes growing CSV segments under `C:\PerfLogs`, and scheduled task `FreezeWatchBoot` successfully restarted it after the AMD-driver reboot.

**Files:**
- Create: `C:\PerfLogs\FreezeWatch*.csv` (collector output)
- Create: scheduled task `FreezeWatchBoot`

**Interfaces:**
- Produces: the only diagnostic that can discriminate the remaining hypotheses on the next freeze. Task 5 reads it.

**Why this is the highest-value action.** No crash dump exists or will exist — `MEMORY.DMP` absent, `Minidump\` empty, `LiveKernelReports\` empty, and `BugCheckProgress 0x00000081` means the dump path aborts too early to persist even the bugcheck parameters. A 1-second CSV counter log flushes each sample to disk, so it **survives a hard power cut**. Cost is ~1 MB/hour and <0.5% CPU. `logman query` currently lists **zero** collector sets, so there is nothing to conflict with.

- [ ] **Step 1: Confirm no conflicting collector exists**

```powershell
logman query
```

Expected: no data collector sets listed.

- [ ] **Step 2: Create the collector (REQUIRES ELEVATION)**

Run in an **elevated** PowerShell 7. One line:

```
logman create counter FreezeWatch -c "\Memory\Available MBytes" "\Memory\Committed Bytes" "\Memory\Pages/sec" "\Memory\Pool Nonpaged Bytes" "\Processor Information(_Total)\% DPC Time" "\Processor Information(_Total)\% Interrupt Time" "\Processor Information(_Total)\DPCs Queued/sec" "\PhysicalDisk(_Total)\Avg. Disk sec/Transfer" "\PhysicalDisk(_Total)\Current Disk Queue Length" "\System\Processor Queue Length" "\System\Context Switches/sec" -si 1 -f csv -o C:\PerfLogs\FreezeWatch -v mmddhhmm -max 500 -cnf 01:00:00
```

- [ ] **Step 3: Start it and make it survive reboots**

```
logman start FreezeWatch
schtasks /create /tn FreezeWatchBoot /tr "logman start FreezeWatch" /sc onstart /ru SYSTEM /rl HIGHEST /f
```

- [ ] **Step 4: Verify it is actually writing**

```powershell
logman query FreezeWatch
Start-Sleep -Seconds 10
Get-ChildItem C:\PerfLogs\FreezeWatch*.csv | Select-Object Name,Length,LastWriteTime
```

Expected: Status `Running`, and a CSV whose `Length` grows between two checks. A collector that exists but writes nothing is worthless — confirm growth, not just existence.

**Rollback (complete removal):**

```
logman stop FreezeWatch
logman delete FreezeWatch
schtasks /delete /tn FreezeWatchBoot /f
```

**Do NOT** leave `wpr.exe` tracing running unattended as a substitute — it consumes 1–3 GB/hour. Reserve it for a supervised window, and only if Task 5 points at the DPC lane.

---

## Task 3: Shed and bound the agent fleet

**Files:** none — host process state.

**Interfaces:**
- Produces: reduced load. This is **not** the proven cause; it is the cheapest variable you control, and removing it makes the next freeze's counter-log signature cleaner to read.

**Framing, honestly:** the node fleet is real and severe (measured 96 → 134 processes in 44 s, Available MBytes touching 143 at one point) but it is **self-recovering** and explains no freeze on its own. At 28 min uptime the host carried 132 `node.exe` and was stable at 4.2 GB free — *more* load than at either freeze.

- [ ] **Step 1: Measure and identify**

```powershell
Get-Process node -ErrorAction SilentlyContinue | Where-Object Path | Group-Object Path |
  Sort-Object Count -Descending | Select-Object Count,Name | Format-Table -AutoSize
(Get-Process).Count
```

Known at last measurement: **121** under `C:\Users\JeremyWilliams\.local\bin\node.exe` (Claude Code / MCP / subagents) and 11 under Cursor.

- [ ] **Step 2: Close sessions, do not kill PIDs**

Close idle Claude Code and Cursor windows through their UI. Killing `node.exe` by PID takes down live MCP servers belonging to sessions still in use, with no safe way to tell which from outside.

- [ ] **Step 3: Check for a background daemon regrowing the fleet**

```bash
npx @claude-flow/cli@latest daemon status --all
```

If running and not wanted: `npx @claude-flow/cli@latest daemon stop`. The daemon spawns headless `claude` sessions on a timer, silently regrowing the node count. It is optional by design.

- [ ] **Step 4: Re-measure**

```powershell
"node: " + (Get-Process node -ErrorAction SilentlyContinue).Count
"procs: " + (Get-Process).Count
"AvailMB: " + [math]::Round((Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue)
```

**No hard gate.** Unlike the superseded plan, this does *not* block Stage B — the ≥8 GB free gate was derived from the refuted memory hypothesis and is withdrawn.

---

## Task 4: Update the AMD Radeon 860M display driver

**Status:** ✅ COMPLETE. AMD Radeon 860M changed from `32.0.13050.18` (2025-04-14, `oem23.inf`) to `32.0.31041.1004` (2026-08-16, `oem5.inf`). FreezeWatch remained `Running` after the required reboot.

**Files:** none — driver package.

**Interfaces:**
- Consumes: nothing. Independent of Tasks 2–3.
- Produces: removal of the single most plausible named source of the `0x133`.

**Why this one and not NVIDIA:** AMD `32.0.13050.18` is dated **2025-04-14**, 16 months old, running under a 2026 Insider kernel; NVIDIA is `32.0.16.1088` dated 2026-07-21 and current. On a laptop the iGPU drives the desktop and is in the DPC path. Cross-examination confirmed providers `amdkmdag`, `amdwddmg`, `amdkmpfd`, `amdlog` **do not exist** on this machine — the AMD stack emits no fault telemetry at all, so its clean record is a measurement gap.

- [ ] **Step 1: Record current state for rollback**

```powershell
Get-CimInstance Win32_PnPSignedDriver -Filter "DeviceClass='DISPLAY'" |
  Select-Object DeviceName,DriverVersion,DriverDate,InfName | Format-Table -AutoSize
```

Write the AMD `DriverVersion` and `InfName` into the task evidence file before changing anything.

- [ ] **Step 2: Obtain the driver**

Prefer the **MSI support page for the Creator A16 AI+ A3HVFG** (OEM-validated for this panel/hybrid-graphics config) over AMD's generic Adrenalin package. If MSI has nothing newer than 2025-04, use AMD's official Radeon 860M package.

- [ ] **Step 3: Install, then reboot once, deliberately**

This is the one sanctioned restart in Stage A. Note the Global Constraint against casual power-cycling still applies — reboot *for the driver install*, not to "clean up."

- [ ] **Step 4: Verify the version changed**

```powershell
Get-CimInstance Win32_PnPSignedDriver -Filter "DeviceClass='DISPLAY'" |
  Select-Object DeviceName,DriverVersion,DriverDate | Format-Table -AutoSize
```

- [ ] **Step 5: Confirm FreezeWatch restarted after the reboot**

```powershell
logman query FreezeWatch
```

Expected `Running` — this proves the `FreezeWatchBoot` task works, which is the whole point of Task 2 Step 3.

**Rollback:** Device Manager → display adapter → Driver → **Roll Back Driver**. If unavailable, DDU in safe mode then reinstall `32.0.13050.18`.

---

## Task 5: Observe, and read the log on the next freeze

**Files:** read `C:\PerfLogs\FreezeWatch*.csv`

**Interfaces:**
- Consumes: Tasks 2 and 4.
- Produces: the verdict that decides whether further structural work (leaving Insider, BIOS) is warranted.

- [ ] **Step 1: If a freeze occurs, read the tail immediately after reboot**

```powershell
Get-ChildItem C:\PerfLogs\FreezeWatch*.csv | Sort-Object LastWriteTime |
  Select-Object -Last 1 | ForEach-Object { Get-Content $_.FullName -Tail 40 }
```

- [ ] **Step 2: Classify the lane**

| Last samples show | Lane |
|---|---|
| `% DPC Time` climbing past ~20–30% and/or `Avg. Disk sec/Transfer` spiking, while `Available MBytes` stays healthy (>2000) | **Driver / DPC** — the driver update did not cover it; escalate to a supervised `wpr` capture |
| `Available MBytes` <300 with `Pages/sec` in the thousands and `Current Disk Queue Length` climbing | **Paging / memory** — the memory lane returns; revisit Task 3 seriously |
| Log stops with every counter flat and nominal | **Neither** — firmware/hardware below the OS; proceed to leaving Insider, then BIOS |

- [ ] **Step 3: Confirm the bugcheck class of the new event**

Always read by **named field**, never positionally — this is the exact mistake that misdirected the original plan:

```powershell
Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Microsoft-Windows-Kernel-Power';Id=41} -MaxEvents 5 |
 ForEach-Object { $x=[xml]$_.ToXml()
   [pscustomobject]@{ Time=$_.TimeCreated
     BugcheckCode=($x.Event.EventData.Data|Where-Object Name -eq 'BugcheckCode').'#text' } }
```

- [ ] **Step 4: If two clean weeks pass with no freeze**

Relax `processors` back to `6` in `.wslconfig` **and** remove `sparseVhd=true` in the same edit (the parked Ruling G), then `wsl --shutdown`.

**Deferred structural options, in order, only if freezes continue after Task 4:** ① leave the Windows Insider channel (first anomaly was 1 day after the 08/15 install; both `0x133`s are on build 26340; the 26340.9212 feature update failed with `0x8024200D`) ② MSI BIOS newer than `E15FKAMS.320` (2026-05-17) — least reversible, do last. **Adding RAM is not on this list** — Freeze #2 refutes that lane.

---

# STAGE B — Port Claude Code and Codex into WSL

Substance unchanged from the original plan; two preflight rulings are now baked in rather than carried separately.

## Task 6: Controlled first boot of Ubuntu-24.04

**Status:** ✅ COMPLETE. Ubuntu boots under the caps: 6,217,277,440 bytes RAM, 2 GiB swap, and `nproc=4`.

**Interfaces:**
- Consumes: Task 1's caps (which *do* govern this VM).
- Produces: a running distro for Tasks 7–13.

- [ ] **Step 1: Arm host-side monitoring in a second window**

```powershell
while ($true) {
  $c = (Get-Counter '\Memory\Committed Bytes').CounterSamples[0].CookedValue/1GB
  $f = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB
  $v = (Get-Process vmmem,vmmemWSL -ErrorAction SilentlyContinue | Measure-Object WorkingSet -Sum).Sum/1GB
  "{0}  commit={1:N1}GB  free={2:N1}GB  vmmem={3:N1}GB" -f (Get-Date -f HH:mm:ss), $c, $f, $v
  Start-Sleep 3
}
```

- [ ] **Step 2: Boot**

```powershell
wsl -d Ubuntu-24.04 -- echo "wsl-up"
```

- [ ] **Step 3: Prove the caps are being read**

```powershell
wsl -d Ubuntu-24.04 -- bash -lc "free -h; nproc"
```

Expected: total memory ≈ 6 GB (not ~15 GB) and `nproc` = **4** (not 16). If `nproc` returns 16, `.wslconfig` was not applied — `wsl --shutdown`, re-check the file, repeat. This is also the empirical test of the `autoMemoryReclaim=dropcache` casing fix from Task 1's fix round.

**Rollback:** `wsl --shutdown`; if it will not stop, `wsl --terminate Ubuntu-24.04`. `wsl --unregister` **destroys the distro and all data in it** — take `wsl --export` first.

---

## Task 7: Verify the WSL runtime baseline

**Status:** ✅ COMPLETE (2026-08-29). `wsl --update` reports the newest WSL channel already installed; Ubuntu packages were fully upgraded (42 packages, zero remaining), `dpkg --audit` is clean, and `jq 1.7`, `git 2.43.0`, `rsync 3.2.7`, Node 22.23.1, npm 10.9.8, and Claude Code 2.1.214 are available. Known upstream warning: WSL 2.9.x leaves `systemd-binfmt.service` failed because `/proc/sys/fs/binfmt_misc/status` is read-only while `WSLInterop` remains functional; do not mask it without an official fix.

**Interfaces:** produces `claude`, `node`, `npx`, `jq`, `git`, `rsync` on PATH. Every later task depends on these; `jq` is required by every bash hook.

A prior mirror exists from 2026-07-14 but is six weeks stale and unverified. Verify, don't assume.

- [ ] **Step 1: Write a self-contained probe** (avoids the inline-variable-eating trap)

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

- [ ] **Step 2: Run it**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "sed 's/\r$//' /mnt/c/Users/JeremyWilliams/AppData/Local/Temp/claude/probe.sh > /tmp/probe.sh && bash /tmp/probe.sh"
```

- [ ] **Step 3: Install anything MISSING**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "sudo apt-get update && sudo apt-get install -y jq rsync git"
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "source ~/.nvm/nvm.sh && npm install -g @anthropic-ai/claude-code"
```

`apt-get` prompts for a sudo password — this step is interactive.

- [ ] **Step 4: Re-run the probe; zero MISSING**

---

## Task 8: Build the manifest and rsync the portable tree

**Files:** create `/home/jeremyw/.claude/sync-from-windows.sh`

**Port arithmetic:** excluding `plugins/` (838.73 MB / 55,591 files of `win32-x64` binaries) and `projects/` (167.13 MB of transcripts) takes the transfer from ~1,030 MB to **~7 MB / ~700 files — a 99.3% reduction.**

The `.claude` tree is already a git repo whose `.gitignore` encodes the MIRROR-vs-exclude split, written with the secret/volatility distinction in mind. Reuse it rather than inventing a second list.

- [ ] **Step 1: Read the existing script before trusting it**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "cat /home/jeremyw/.claude/sync-from-windows.sh 2>/dev/null || echo ABSENT"
```

Confirm it carries **anchored** excludes for at least `.credentials.json`, `/projects/`, `/plugins/`, `/backups/`, `/daemon/`, `/sessions/`. If any are missing, replace it.

- [ ] **Step 2: Write the new script**

```bash
#!/usr/bin/env bash
set -euo pipefail
SRC=/mnt/c/Users/JeremyWilliams/.claude/
DST=/home/jeremyw/.claude/

rsync -av \
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
  --exclude='/.superpowers/' \
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

> **Ruling B applied — `--delete-excluded` is deliberately absent.** It would delete destination files matching exclude patterns, and the script excludes `/settings.json` and `/CLAUDE.md` — so it would **destroy the hand-authored Linux settings and CLAUDE.md** from the June mirror, the very files excluded so they would persist. The destination is a superset we add to, not a mirror we enforce. Revisit `--delete` only after Tasks 10 and 12 re-author those files, and only after inspecting a dry run.

- [ ] **Step 3: Dry-run and check the size**

Add `--dry-run` to the rsync line and run it. **Gate: total under ~20 MB.** Hundreds of MB means an exclude is wrong.

- [ ] **Step 4: Run in batches**

First pass with `--exclude='/_archive/'` added; confirm the host monitor stays flat; then re-run without it.

- [ ] **Step 5: Verify**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "du -sh /home/jeremyw/.claude; find /home/jeremyw/.claude/skills -type f | wc -l"
```

Expected ~7 MB, `skills/` with ~276 files.

**Note:** `agents/` and `commands/` are **empty** on the Windows side despite what `CLAUDE.md` claims. Create them empty for parity; do not report them as ported content.

---

## Task 9: Port the two shell scripts

> **Ruling A applied — this task runs BEFORE the settings file that references it.** The original plan wired `settings.json` to these scripts one task *before* creating them, leaving a window where a **blocking** `PreToolUse` hook pointed at a nonexistent file, failing every Bash tool call.

**Files:** create `/home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh` and `/home/jeremyw/.claude/statusline.sh`

- [ ] **Step 1: Port the secret scanner**

Base it on the `PreToolUse` "git commit" entry in `hooks/legacy-linux-hooks.json.reference` (9,897 bytes) — the Linux ancestor of the current PowerShell hooks, already implementing these patterns in bash. Port the five vendor prefixes (`ghp_`, `sk-proj-`, `sk-ant-`, `ntn_`, `tvly-`) plus the generic `api[_-]?key|secret|password|token|private[_-]?key` assignment regex via `grep -E`.

**Preserve the fail-open contract** — the PowerShell original exits 0 on internal error. A blocking hook that fails closed breaks every Bash call.

- [ ] **Step 2: Test both directions**

```bash
echo '{"tool_input":{"command":"echo ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}}' | bash /home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh; echo "exit=$?"
echo '{"tool_input":{"command":"ls -la"}}' | bash /home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh; echo "exit=$?"
```

First must flag; second must exit 0 silently. **Both cases required** — a scanner that blocks everything is as broken as one that blocks nothing.

- [ ] **Step 3: Port the statusline**

`statusline.ps1` declares `#Requires -Version 7.0` and uses .NET APIs (`[System.IO.Path]::GetRelativePath`, `[Console]::In`) — not portable even with pwsh installed. Its header says it is a port *of* `statusline-developer.sh`; prefer recovering that original, or reuse `helpers/statusline.js`. Otherwise read stdin with `jq`: `.model.display_name`, `.output_style.name`, `.workspace.current_dir`, `.workspace.project_dir`, then `git rev-parse` / `symbolic-ref` / `status --porcelain`. Keep the same ANSI codes.

- [ ] **Step 4: Test it**

```bash
echo '{"model":{"display_name":"Opus 5"},"output_style":{"name":"Proactive"},"workspace":{"current_dir":"/home/jeremyw","project_dir":"/home/jeremyw"}}' | bash /home/jeremyw/.claude/statusline.sh
```

- [ ] **Step 5: `chmod +x` both**

**Do not port** `hooks/post-edit-console-log.ps1` or `hooks/post-edit-format.ps1` — referenced by **no** hook in `settings.json`, already dead on Windows. `hooks/backup-commit.ps1` is driven by Task Scheduler, not settings, so it will not show in a settings-only audit; if WSL should self-backup, port it with `repo=/home/jeremyw/.claude` on cron or `systemd --user`.

---

## Task 10: Author the WSL settings.json

**Files:** create `/home/jeremyw/.claude/settings.json`

Authored, never copied: two hooks are `critical` breakages under Linux, and the `PreToolUse` secret scanner is **blocking** on matcher `Bash`.

- [ ] **Step 1: Rewrite the four node hook paths**

The JS is portable — `skill-router.js` already prefers `process.env.HOME` over `USERPROFILE`. Pure path rewrite:

| JSON pointer | New command |
|---|---|
| `hooks.PreToolUse[1].hooks[0].command` | `node /home/jeremyw/.claude/hooks/ccg/subagent-context.js` |
| `hooks.UserPromptSubmit[0].hooks[0].command` | `node /home/jeremyw/.claude/hooks/ccg/workflow-state.js` |
| `hooks.UserPromptSubmit[0].hooks[1].command` | `node /home/jeremyw/.claude/hooks/ccg/skill-router.js` |
| `hooks.SessionStart[0].hooks[0].command` | `node /home/jeremyw/.claude/hooks/ccg/session-start.js` |

Preserve existing `matcher` and `timeout` values verbatim.

- [ ] **Step 2: Point at the Task 9 scripts**

- `hooks.PreToolUse[0].hooks[0].command` → `bash /home/jeremyw/.claude/hooks/pre-commit-secret-scan.sh`
- `statusLine.command` → `bash /home/jeremyw/.claude/statusline.sh`

- [ ] **Step 3: Fix permissions**

- **Delete** `permissions.allow[6]` — the `PowerShell(...)` tool prefix does not exist on Linux and `set_title.ps1` has no Linux counterpart.
- **Rewrite** `permissions.allow[7]` → `Bash(npx @claude-flow/cli@latest hooks worker dispatch --trigger audit)`, else it silently stops matching and starts prompting.
- **Drop** `permissions.allow[4]` (`Bash(*codeagent-wrapper*)`) unless a Linux build is installed.
- In `settings.local.json`: `Read(C:/Users/JeremyWilliams/**)` → `Read(/home/jeremyw/**)`; collapse the seven git rules to `Bash(git -C /home/jeremyw/.claude:*)`; **delete** the `pwsh`, `powershell.exe`, and both `Read(//g/My Drive/...)` rules.

- [ ] **Step 4: Marketplaces and plugins**

- **Drop** `extraKnownMarketplaces.gitkraken` — the only `directory`-source marketplace of 15, pinned to a `C:\` path.
- **Set** `enabledPlugins["gitkraken-hooks@gitkraken"] = false` — its `hooks.json` embeds `gk-alpha.exe` ten times.
- **Keep** the remaining `enabledPlugins` (150 entries) and 14 git-sourced marketplaces verbatim.

- [ ] **Step 5: Port the `env` block verbatim**

6 vars, no paths. Ensure `BRIGHTDATA_MCP_TOKEN` is exported in the WSL shell profile — do **not** copy Windows env-var *values* into a WSL `.env`; that creates a second copy of secrets that currently exist in exactly one place.

- [ ] **Step 6: Validate**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "jq empty /home/jeremyw/.claude/settings.json && jq -r '.hooks | to_entries[] | .value[].hooks[].command' /home/jeremyw/.claude/settings.json"
```

Expected: no parse error, and **zero** lines containing `pwsh`, `powershell`, or `C:/`.

---

## Task 11: Place the memory store at the correct Linux slug

**Files:** create `/home/jeremyw/.claude/projects/<linux-slug>/memory/`

The file-memory store — the documented "system of record" — is keyed by a **slugified working directory**. Windows uses `C--Users-JeremyWilliams`; under WSL the cwd is `/home/jeremyw`, so the slug differs. Copied to the Windows-named directory, all 7 memory files are **silently never read**. This is the most likely thing to half-work and be mistaken for success.

- [ ] **Step 1: Discover the slug empirically — do not guess**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "cd /home/jeremyw && claude -p 'reply with the single word ok' >/dev/null 2>&1; ls /home/jeremyw/.claude/projects/"
```

- [ ] **Step 2: Copy into it**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 -- bash -lc "SLUG=\$(ls /home/jeremyw/.claude/projects/ | head -1); mkdir -p \"/home/jeremyw/.claude/projects/\$SLUG/memory\"; cp /mnt/c/Users/JeremyWilliams/.claude/projects/C--Users-JeremyWilliams/memory/*.md \"/home/jeremyw/.claude/projects/\$SLUG/memory/\"; ls -la \"/home/jeremyw/.claude/projects/\$SLUG/memory/\""
```

Expected 7 files: `MEMORY.md` plus `agentbox-ruflo-windows-setup.md`, `ccg-multi-model-local-setup.md`, `claude-config-restore-2026-07.md`, `claude-flow-v3-core-repo.md`, `omc-setup-preserve-2026-07.md`, `wsl-claude-config-mirror.md`.

- [ ] **Step 3: Correct facts that are now wrong**

Rewrite `wsl-claude-config-mirror.md` for the new sync script and corrected slug; note in `claude-config-restore-2026-07.md` that its paths are Windows-side.

- [ ] **Step 4: Verify it loads**

Start a WSL Claude session in `/home/jeremyw` and confirm the `MEMORY.md` index appears in context. If not, the slug is wrong — return to Step 1.

---

## Task 12: Author the WSL CLAUDE.md and re-register MCP servers

- [ ] **Step 1: Author CLAUDE.md — invert, don't copy**

The Windows file would **actively mis-instruct** a Linux session: its shell-syntax section forbids `realpath`, `jq`, `$(pwd)`, `/dev/null`, `2>/dev/null` and mandates PowerShell cmdlets — exactly backwards in WSL. Changes: machine → WSL2 Ubuntu-24.04, user `jeremyw`, home `/home/jeremyw`; shell → bash, **inverting** the shell-notes block; repos → `/home/jeremyw/repos` (native ext4 strongly preferred over `/mnt/c`); **delete** every `G:\My Drive` backup instruction; correct the Directory Structure section (`agents/`, `commands/` empty; `todos/` absent).

- [ ] **Step 2: Register the three portable MCP servers**

Use `mcp-scaffold.json` — the documented, secret-free blueprint. **Omit GitKraken** (hardcodes `gk-alpha.exe`).

```bash
claude mcp add-json sequential-thinking '{"type":"stdio","command":"npx","args":["-y","@modelcontextprotocol/server-sequential-thinking"]}' --scope user
claude mcp add-json Context7 '{"type":"stdio","command":"npx","args":["-y","@upstash/context7-mcp"]}' --scope user
claude mcp add-json chrome-devtools '{"type":"stdio","command":"npx","args":["chrome-devtools-mcp@latest"]}' --scope user
```

- [ ] **Step 3: Verify** — `claude mcp list` shows three servers Connected.

- [ ] **Step 4: Handle `rules/ccg-skill-routing.md`**

It contains 41 absolute paths to `skills/ccg/domains/` — a directory that **does not exist even on Windows**. Dead today, costing tokens every session. Either drop it from the WSL rules set or reinstall `ccg-workflow` in WSL and regenerate it. **Fix this on the Windows side too** — it is a live bug there.

---

## Task 13: Interactive completion

- [ ] **Step 1: Authenticate** — run `claude`, then `/login`. `.credentials.json` is never copied.
- [ ] **Step 2: Let plugins reinstall** — Claude Code re-clones the 14 git marketplaces and reinstalls from `enabledPlugins`, fetching `linux-x64` optional deps (`@esbuild/linux-x64`, `@img/sharp-linux-x64`, `@ast-grep/napi-linux-x64-gnu`, `@rollup/rollup-linux-x64-gnu`). Several minutes, a few hundred MB.
- [ ] **Step 3: Re-authorize connectors** — 44 `claude.ai` connectors are OAuth-side with no `command`/`args` to rewrite. Print the list from `.claude.json` → `claudeAiMcpEverConnected` first, then reconnect only those actually needed in WSL.
- [ ] **Step 4: Final verification**
  - [ ] `claude mcp list` → 3 stdio servers Connected
  - [ ] A trivial Bash tool call → the `PreToolUse` secret hook does **not** error
  - [ ] Statusline renders
  - [ ] `MEMORY.md` loads in a session started at `/home/jeremyw`
  - [ ] Host monitor: `vmmem` ≤6 GB, free RAM stable
  - [ ] `jq -r '..|.command?//empty' ~/.claude/settings.json` shows no `pwsh` or `C:/`
  - [ ] `logman query FreezeWatch` still `Running`

---

## Task 14: Install native Codex in WSL

**Status:** ✅ COMPLETE (2026-08-29). Native `@openai/codex@0.151.0` is installed under the WSL nvm Node 22 prefix and resolves to `/home/jeremyw/.nvm/versions/node/v22.23.1/bin/codex`, not the Windows shim exposed through `/mnt/c`.

**Rules:**
- Match the verified Windows CLI version before migrating config.
- Never use `/mnt/c/Users/JeremyWilliams/.local/bin/codex` as the WSL runtime.
- Never copy Windows `auth.json`; WSL authenticates independently.

---

## Task 15: Translate the Windows Codex configuration

**Status:** ✅ COMPLETE (2026-08-29). Linux-native TOML, AGENTS guidance, hooks, portable skills/agents/rules, personal marketplace metadata, and 91 small authored plugin bundles are installed. Windows caches, app-server runtime, auth, sessions, and machine state were excluded.

**Files:**
- Create `/home/jeremyw/.codex/config.toml`
- Create `/home/jeremyw/.codex/AGENTS.md`
- Create `/home/jeremyw/.codex/sync-from-windows.sh`
- Mirror portable roots: `agents/`, `skills/`, `prompts/`, `rules/`

**Portable declarative state:**
- Preserve top-level model/reasoning/approval/sandbox/service-tier choices, except the Windows-only `notify` executable.
- Preserve plugin enablement only for OpenAI-curated plugins and the portable `codex-marketplace-global` personal catalog.
- Drop every Windows Git marketplace snapshot. Live validation showed the copied Claude-oriented repositories do not contain a supported Codex marketplace manifest; Codex automatically discovers `~/.agents/plugins/marketplace.json` instead.
- Preserve `[features]`, `[memories]`, and OS-neutral TUI values.
- Preserve portable MCP definitions: Composio, Context7, sequential-thinking, grok, amplitude, amplitude-com, comfy-cloud, and chrome-devtools.
- Drop machine-local MCP definitions: Codex App `node_repl`, GitKraken `.exe`, `devfleet` localhost, plugin-root-dependent `ruflo`/`t`, and `runapi` because its secret value must not be copied.
- Drop `[desktop]`, `[windows]`, all Windows `[projects.*]`, `[hooks.state.*]` trusted hashes, and Windows node-repl shell-environment paths.
- Recreate only portable shell policy values (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, `CLAUDE_FLOW_*`, `ECC_DISABLED_HOOKS`).

**Never copy:** `auth.json`, `.codex-global-state.json*`, `installation_id`, `cap_sid`, `.sandbox*`, `secrets/`, `sessions/`, `archived_sessions/`, `browser/`, `computer-use/`, `mcp-oauth-locks/`, `sqlite/`, `*.sqlite*`, `history.jsonl`, `session_index.jsonl`, plugin `cache/`, `.plugin-appserver/`, plugin staging/snapshots, `tmp/`, attachments, logs, worktrees, or thread/process-manager state. The small top-level authored plugin bundles referenced by the personal marketplace are portable and may be copied explicitly.

- [x] Back up any pre-existing WSL `.codex` declarative files (none existed; no backup was needed).
- [x] Dry-run/reconcile the portable rsync; final portable payload is about 12 MB and contains no excluded cache/app-server/auth/session state.
- [x] Mirror portable roots and install the translated TOML/AGENTS/sync script.
- [x] Parse-test `config.toml` with native Codex (`codex --version`, `codex mcp list`, `codex plugin list --available --json`).
- [x] Verify no `C:\\`, `C:/`, `G:\\`, `.exe`, `auth.json`, or literal secret-bearing MCP env values remain.

---

## Task 16: Authenticate and verify WSL Codex

**Status:** ⏸ READY FOR USER LOGIN (2026-08-29). All non-secret verification is complete. WSL Codex correctly reports `Not logged in`; authentication is intentionally not copied or automated.

- [ ] Run `codex login` interactively in WSL; do not copy the Windows auth file.
- [ ] Re-authenticate remote OAuth MCP servers only when needed (Composio, Figma, Vercel, Amplitude, Comfy Cloud).
- [ ] Install only verified Codex-compatible marketplace plugins after login; do not re-add the incompatible Claude Git marketplace declarations or copy native cache state.
- [x] Verify `command -v codex` points under `/home/jeremyw/.nvm/`, `codex --version` is `0.151.0`, config parses, portable MCPs enumerate, and no Windows paths appear in `/home/jeremyw/.codex/config.toml`.
- [x] Keep Codex Desktop on Windows separate from Codex CLI in WSL; desktop-only browser/CUA/notification settings are intentionally not portable.

---

## Open Decisions

1. **`_archive/`** (1.52 MB) — the only place the deduped agents exist. Copy as insurance (default), or promote a curated subset back into `agents/`?
2. **`ai-stack-sync/`** — make it the ongoing Windows↔WSL sync mechanism rather than a one-shot rsync?
3. **`repos/`** — clone natively into `/home/jeremyw/repos` (fast) or reach Windows repos via `/mnt/c` (slow, single source of truth)?
4. **`chrome/chrome-native-host.bat`** — Claude-in-Chrome from WSL needs the native host registered Windows-side and reached over localhost. Excluded by default.
5. **Cowork VM** — it runs uncapped by design (`.wslconfig` cannot govern it) and was alive through Freeze #1. Worth deciding whether it should stay resident when idle.
6. **Insider channel** — deferred structural option ① if freezes continue after Task 4.

---

## Self-Review

**Spec coverage.** Freeze root-cause (run `wf_397ebfe5-97b`) → Tasks 2–5; config recon (run `wf_8179a4e4-0ba`, 62 findings) → Tasks 8–13. The six errors in the superseded plan are each corrected in "What Changed and Why" rather than silently dropped, as the synthesis required.

**Ordering.** Ruling A is now structural: Task 9 (create scripts) precedes Task 10 (wire them). Ruling B is inlined at Task 8 Step 2 with its rationale, so a future editor cannot re-add `--delete-excluded` without reading why it was removed.

**Withdrawn.** The "≥8 GB free RAM" gate is gone — it derived from the refuted memory hypothesis. Task 3 is now load hygiene, not a blocker.

**Known gap.** Task 9 Step 3 depends on recovering `statusline-developer.sh`, which has not been located; fallback is a fresh `jq` port with the `.ps1` as behavioural reference.

**Honest limit carried from the synthesis.** The specific driver whose DPC overran **cannot be named from logs**, now or later. Task 4 is a reversible bet on the oldest driver in the DPC path, not a confirmed fix; Task 5 exists precisely because that bet may fail.
