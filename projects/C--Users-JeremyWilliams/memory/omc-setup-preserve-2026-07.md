---
name: omc-setup-preserve-2026-07
description: OMC runs in global-preserve mode; upgraded 4.15.4 -> 5.0.2 on 2026-08-28 (v5 retires ultrawork and fails graph exec closed on Windows).
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5354cfbf-5851-4146-ab30-5fd71c078545
  modified: 2026-08-29T00:24:19.211Z
---

oh-my-claudecode (OMC) is set up on this machine in **global-preserve** mode: base `~/.claude/CLAUDE.md` (Ruflo config) is untouched except one `<!-- OMC:IMPORT:START -->@CLAUDE-omc.md<!-- OMC:IMPORT:END -->` block at the end; OMC's canonical instructions live in `~/.claude/CLAUDE-omc.md`. Custom `statusline.ps1` kept — OMC HUD skipped (no tmux on native Windows). Team defaults 3/claude, `taskTool=builtin`.

**Upgraded 2026-08-28: 4.15.4 → 5.0.2.** Update path that works here (the marketplace is a git clone, so it must be refreshed *before* the plugin resolves a new version):
`claude plugin marketplace update omc` → `claude plugin update oh-my-claudecode@omc` → restart. Both version caches are kept under `plugins/cache/omc/oh-my-claudecode/`, so rollback to 4.15.4 is just re-pointing at that dir. Then re-run the *new* version's installer with an explicit root:
`OMC_SETUP_PLUGIN_ROOT=<5.x root> bash <5.x root>/scripts/setup-claude-md.sh global preserve` — always `global preserve`, never `local`: cwd is `C:\Users\JeremyWilliams`, so `.claude/CLAUDE.md` resolves to the *global* curated file and `local` mode would overwrite it.

**Resolved:** the 4.15.4 gotcha (published plugin missing `bridge/claude-md-coordinator.cjs`, forcing a manual esbuild rebuild) does NOT recur in 5.0.2 — the coordinator ships and setup exits 0 with "Plugin verified". Keep the rebuild recipe in mind only if a future version regresses.

**v5 breaking changes that touched this config:** `ultrawork` and the whole `defaultExecutionMode` key were removed in 5.0.0 and are read by no runtime surface — the dead value was cleared from `.omc-config.json` per the installer's own Step 2.4. `omc-reference` was replaced by the `wiki` skill (installed to `~/.claude/skills/wiki/SKILL.md`). Also retired: ultraqa, ultrapilot, and OMC's own swarm/pipeline/deep-dive/sciomc/ccg/omc-teams/learner/writer-memory — note these are *OMC-namespaced* names only; the unrelated CCG toolchain and ruflo swarm are untouched.

**Windows caveat:** 5.0.2 intentionally **fails closed for graph execution on Windows and macOS** (no safe directory-descriptor primitive); only Linux runs graphs. Don't debug graph features here — they are disabled by design.

**Known false positive:** the installer prints "Found legacy OMC hook entries in settings.json" on every run. Verified 2026-08-28 — untrue. `~/.claude/settings.json` contains no OMC hooks at all; its only OMC references are the `oh-my-claudecode@omc: true` enable flag and the `omc` marketplace URL, both required. Hooks present are CCG (`hooks/ccg/*.js`) plus `pre-commit-secret-scan.ps1`. Ignore the warning; do not delete anything.

`omc` CLI (`oh-my-claude-sisyphus`, npm latest 5.0.2) installed but `better-sqlite3` native build was blocked by npm allowScripts → run `npm install -g --allow-scripts=better-sqlite3` if SQLite features fail. Related: [[claude-config-restore-2026-07]].
