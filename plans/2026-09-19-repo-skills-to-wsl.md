# Repo-Scoped Skills → WSL Claude Code — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Copy the 8 directory-scoped skills that live at `C:\Users\JeremyWilliams\repos\.claude\skills\` into the WSL Ubuntu-24.04 Claude Code install, so they load automatically for the WSL-native projects under `~/repos\` the same way they already load for Windows-side work under `C:\Users\JeremyWilliams\repos\`.

**Architecture:** One-way rsync copy, run from inside WSL, from the Windows tree (visible at `/mnt/c/Users/JeremyWilliams/repos/.claude/skills/`) to a new native WSL path (`/home/jeremyw/repos/.claude/skills/`). Windows stays the single source of truth — this mirrors the existing `~/.claude/sync-from-windows.sh` pattern but for the directory-scoped `repos/.claude/` tree, which that script does not touch. A small idempotent helper script is added so this isn't a one-off that goes stale, matching the convention already established for the global `~/.claude` sync.

**Tech Stack:** WSL2 Ubuntu 24.04 (`jeremyw`, `/home/jeremyw`), bash, rsync, sha256sum.

**Spec:** None — this is an ops/config task, not a code feature, derived directly from investigation of both filesystems (see Global Constraints for the findings that shape it).

## Global Constraints

- **Do not modify anything under `C:\Users\JeremyWilliams\repos\.claude\skills\`.** Windows is authoritative; this is a one-way copy outward, never a merge back.
- **Do not put these skills in `~/.claude/skills/` (global).** They are directory-scoped skills (per `repos\CLAUDE.md` convention: "load only when working under `repos\`") and must land at `<repos-root>/.claude/skills/` on the WSL side to preserve that scoping — mixing them into the global 64-skill WSL set would make them load for every project, not just ones under `~/repos/`.
- **Destination root is `/home/jeremyw/repos/`, not `/mnt/c/Users/JeremyWilliams/repos/`.** WSL already has native clones of a subset of repos (`chimacomics`, `dobeu-knowledge-pilot`, `kepler`, `new-dobeu-net`, `routeready`) at `/home/jeremyw/repos/`; the whole point of the move is to make the skills available natively there without depending on the `/mnt/c` passthrough.
- Verified precondition: all 8 skills are single `SKILL.md` files (no subdirectories, no asset files) and contain zero hardcoded Windows-style paths (`C:\`, `C:/Users`, `G:\`) — confirmed by grep before writing this plan. No path-rewriting step is needed.
- Driving WSL from the Git-Bash `Bash` tool requires `MSYS_NO_PATHCONV=1` on the invoking command; inline `$VAR` inside `wsl.exe -- bash -lc '...'` can expand to empty — prefer literal absolute paths in the inline command, or a script file for anything with variables.
- Transfer budget: 8 small text files, well under 100 KB total. If `rsync` reports materially more than that, stop — something unexpected (a nested asset dir, a stray large file) got picked up.

---

## File Structure

| Path | Responsibility | Action |
|---|---|---|
| `/home/jeremyw/repos/.claude/skills/` | New destination holding the 8 copied skills | Create |
| `/home/jeremyw/.claude/sync-repo-skills.sh` | Idempotent re-sync helper, mirrors `sync-from-windows.sh`'s pattern for this one extra tree | Create |

No files are modified on the Windows side.

---

### Task 1: Create the destination directory and dry-run the copy

**Files:**
- Create: `/home/jeremyw/repos/.claude/skills/` (directory, via the rsync in Step 2)

**Interfaces:**
- Consumes: source tree `/mnt/c/Users/JeremyWilliams/repos/.claude/skills/` (read-only)
- Produces: destination tree `/home/jeremyw/repos/.claude/skills/`, consumed by Task 2's verification

- [ ] **Step 1: Dry-run the rsync to confirm exactly what would transfer**

Run from Git-Bash:

```bash
MSYS_NO_PATHCONV=1 wsl.exe -- bash -lc "rsync -avn --exclude='.git/' /mnt/c/Users/JeremyWilliams/repos/.claude/skills/ /home/jeremyw/repos/.claude/skills/"
```

Expected: a file list showing exactly 8 directories and 8 `SKILL.md` files (`bright-data-best-practices/SKILL.md`, `bright-data-mcp/SKILL.md`, `brightdata-local-search/SKILL.md`, `browser/SKILL.md`, `data-feeds/SKILL.md`, `scrape/SKILL.md`, `search/SKILL.md`, `skill-builder/SKILL.md`), total size well under 1 MB. If anything else appears (extra files, large sizes), stop and re-check the source tree before proceeding.

- [ ] **Step 2: Run the real copy**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -- bash -lc "mkdir -p /home/jeremyw/repos/.claude && rsync -av --exclude='.git/' /mnt/c/Users/JeremyWilliams/repos/.claude/skills/ /home/jeremyw/repos/.claude/skills/"
```

Expected: rsync reports 8 files transferred, exit code 0.

- [ ] **Step 3: Commit checkpoint — none (no git repo involved; this is a filesystem copy, not a code change)**

Skip commit for this task; verification happens in Task 2.

---

### Task 2: Verify byte-for-byte integrity and structural validity

**Files:**
- Test: no test file — verification is done via shell commands directly (this is a data-copy task, not code, so "the test" is a checksum + structural diff rather than a unit test)

**Interfaces:**
- Consumes: source tree `/mnt/c/Users/JeremyWilliams/repos/.claude/skills/`, destination tree `/home/jeremyw/repos/.claude/skills/` (both from Task 1)
- Produces: a pass/fail verification result consumed by this plan's completion criteria

- [ ] **Step 1: Write the verification check (the "test")**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -- bash -lc "diff -rq /mnt/c/Users/JeremyWilliams/repos/.claude/skills/ /home/jeremyw/repos/.claude/skills/"
```

- [ ] **Step 2: Run it and confirm it passes (there is no prior "RED" state to check here — Task 1's copy already ran, so this step is the equivalent of GREEN)**

Expected: no output (empty diff = identical trees). Any output naming a file means Task 1's copy is incomplete or was tampered with — re-run Task 1 Step 2 before continuing.

- [ ] **Step 3: Structural validation — confirm every copied `SKILL.md` still has valid YAML frontmatter**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -- bash -lc "for f in /home/jeremyw/repos/.claude/skills/*/SKILL.md; do head -1 \"\$f\" | grep -q '^---\$' && echo \"OK: \$f\" || echo \"MISSING FRONTMATTER: \$f\"; done"
```

Expected: 8 `OK:` lines, zero `MISSING FRONTMATTER:` lines.

- [ ] **Step 4: Commit checkpoint — none**

No git repo tracks `~/repos/.claude/`; nothing to commit. (The existing `.claude-wsl-backup.git` at `/home/jeremyw/.claude-wsl-backup.git` tracks `~/.claude` only, confirmed during investigation — it is unrelated to this tree and must not be pointed at it.)

---

### Task 3: Add a re-runnable sync helper so this doesn't go stale

**Files:**
- Create: `/home/jeremyw/.claude/sync-repo-skills.sh`

**Interfaces:**
- Consumes: nothing (self-contained script, no arguments)
- Produces: re-runs the same rsync as Task 1 Step 2; safe to invoke any time the Windows-side `repos\.claude\skills\` set changes

- [ ] **Step 1: Write the script**

```bash
#!/usr/bin/env bash
set -euo pipefail

SRC=/mnt/c/Users/JeremyWilliams/repos/.claude/skills/
DST=/home/jeremyw/repos/.claude/skills/

mkdir -p "$DST"
rsync -av --exclude='.git/' "$SRC" "$DST"

echo '[sync] repo-scoped skills refreshed from Windows repos\.claude\skills\'
```

Save this to `/home/jeremyw/.claude/sync-repo-skills.sh` via:

```bash
MSYS_NO_PATHCONV=1 wsl.exe -- bash -lc "cat > /home/jeremyw/.claude/sync-repo-skills.sh << 'SCRIPT_EOF'
#!/usr/bin/env bash
set -euo pipefail

SRC=/mnt/c/Users/JeremyWilliams/repos/.claude/skills/
DST=/home/jeremyw/repos/.claude/skills/

mkdir -p \"\$DST\"
rsync -av --exclude='.git/' \"\$SRC\" \"\$DST\"

echo '[sync] repo-scoped skills refreshed from Windows repos\.claude\skills\'
SCRIPT_EOF
chmod +x /home/jeremyw/.claude/sync-repo-skills.sh"
```

- [ ] **Step 2: Run it once to confirm it's idempotent**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -- bash -lc "/home/jeremyw/.claude/sync-repo-skills.sh"
```

Expected: rsync reports 0 files transferred (already up to date from Task 1), script prints the `[sync]` confirmation line, exit code 0.

- [ ] **Step 3: Verify the script is executable and correctly placed**

```bash
MSYS_NO_PATHCONV=1 wsl.exe -- bash -lc "ls -la /home/jeremyw/.claude/sync-repo-skills.sh"
```

Expected: `-rwxr-xr-x` permissions shown.

- [ ] **Step 4: No commit** — `/home/jeremyw/.claude/` is not the git-tracked config tree for this purpose (that's the Windows-side canonical repo per global CLAUDE.md); this script is WSL-local infrastructure, analogous to the existing `sync-from-windows.sh` which is itself excluded from the sync it performs.

---

## Completion Criteria

- [ ] `/home/jeremyw/repos/.claude/skills/` contains exactly the same 8 skills, byte-identical to the Windows source (Task 2, Step 2 passes with empty diff).
- [ ] All 8 copied `SKILL.md` files have valid frontmatter (Task 2, Step 3).
- [ ] `/home/jeremyw/.claude/sync-repo-skills.sh` exists, is executable, and re-running it is a no-op (Task 3).
- [ ] Nothing under `C:\Users\JeremyWilliams\repos\.claude\skills\` was modified.
