---
name: omc-setup-preserve-2026-07
description: OMC installed in global-preserve mode; v4.15.4 shipped without the CLAUDE.md coordinator artifact (had to rebuild it).
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5354cfbf-5851-4146-ab30-5fd71c078545
  modified: 2026-07-19T15:48:09.203Z
---

oh-my-claudecode (OMC) was set up on this machine 2026-07-19 in **global-preserve** mode: base `~/.claude/CLAUDE.md` (Ruflo config) is untouched except one `<!-- OMC:IMPORT:START -->@CLAUDE-omc.md<!-- OMC:IMPORT:END -->` block at the end; OMC's canonical instructions live in `~/.claude/CLAUDE-omc.md` (loaded only via the `omc` wrapper, not plain `claude`). Byte-identical backup `CLAUDE.md.backup.*` created. `.omc-config.json`: `defaultExecutionMode=ultrawork`, team defaults 3/claude, `taskTool=builtin`, `setupCompleted` set. Agent teams already enabled. Custom `statusline.ps1` kept — OMC HUD skipped (no tmux on native Windows).

**Gotcha:** the published plugin `plugins/cache/omc/oh-my-claudecode/4.15.4` shipped WITHOUT `bridge/claude-md-coordinator.cjs`, which `scripts/setup-claude-md.sh` requires (it refuses all shell/Write fallbacks). Rebuilt it from `src/cli/claude-md-coordinator.ts` using the plugin's own build recipe (esbuild, target node20, cjs, `external: node:crypto/fs/path`, `define` embeds package version + sha256 of `docs/CLAUDE.md`). If a future OMC version is missing this artifact again, rebuild the same way. `omc` CLI (`oh-my-claude-sisyphus`) installed but `better-sqlite3` native build was blocked by npm allowScripts → run `npm install -g --allow-scripts=better-sqlite3` if SQLite features fail.

The installer also flagged legacy OMC hook entries (keyword-detector/stop-continuation/persistent-mode/session-start) in `~/.claude/settings.json` — left untouched; optional manual cleanup. Related: [[claude-config-restore-2026-07]].
