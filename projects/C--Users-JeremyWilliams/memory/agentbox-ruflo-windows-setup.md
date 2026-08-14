---
name: agentbox-ruflo-windows-setup
description: AgentBox + Ruflo are set up on this Windows host; key Windows-specific fixes and the pending cloud-provider step.
metadata: 
  node_type: memory
  type: project
  originSessionId: 23897111-d776-488d-9875-f62aa14d3dc6
  modified: 2026-08-14T12:34:53.672Z
---

AgentBox (`@madarco/agentbox` v0.26.1) and Ruflo (`ruflo` v3.32.0) are installed and working on this native-Windows host (Docker provider; WSL Ubuntu-24.04 exists but is stopped/unused). Set up 2026-07-16. Tutorial artifact: https://claude.ai/code/artifact/a9373e4b-3be3-4c1e-8648-aa7f91a93cbe

**Windows-specific facts (durable, non-obvious):**
- **Box-seed rsync fails on `~/.agents` skill symlinks.** `agentbox create/claude` rsyncs `~/.claude` into the box and treats any non-zero rsync exit as fatal (container torn down → box shows "missing"). Absolute-path symlinks under `~/.claude/skills/` pointing into `~/.agents/skills/` don't resolve in the Linux helper → rsync code 23. Fix: dereference them to real dirs (`rm ~/.claude/skills/<s> && cp -rL ~/.agents/skills/<s> ~/.claude/skills/<s>`). If a sync script recreates the symlinks, this breaks again — re-apply.
- **`CODEX_BIN_PATH` must point at the native `codex.exe`** for `agentbox install codex` / codex detection to work (bare `codex` spawn can't resolve the `.cmd` shim on Windows). Persisted as a User env var → `...\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin\codex.exe`.
- **`codex` on PATH was a name-squatter until 2026-08-14.** npm global prefix is `C:\Users\JeremyWilliams\.local\bin`, and `codex@0.2.3` (an unrelated *static-site generator*) owned that name — so bare `codex app-server` printed help and exited. The `openai-codex` plugin (`scripts/lib/app-server.mjs:190`) spawns bare `"codex"` and **never reads `CODEX_BIN_PATH`**, so the env var did not save it; every stop-time review failed with the misleading `codex app-server connection closed`. Fixed by `npm rm -g codex && npm i -g @openai/codex` (→ codex-cli 0.147.0 on PATH). If that error returns, check `npm ls -g --depth=0 | grep codex` before suspecting auth or network.
- **npm 12 blocks postinstall scripts by default** — opencode-ai needs `--allow-scripts=opencode-ai,@homebridge/node-pty-prebuilt-multiarch`.
- **Ruflo MCP deduped**: removed the standalone `ruflo` (local scope); kept `plugin:ruflo-core:ruflo`. `ruflo doctor` warns "MCP Servers: ruflo not found" — that's a false positive (naive name match); do NOT re-add the standalone.

**In-box agents**: claude/codex/opencode all present + AgentBox Codex plugin enabled in `~/.codex/config.toml`. Grok & Gemini can't run in a box (rescue lanes only — grok MCP plugin + `grok:/codex:/gemini:rescue` skills, all authed).

**Pending (needs Jeremy's accounts):** E2B (`agentbox e2b login`, key from e2b.dev) and Vercel (`agentbox vercel login` — needs VERCEL_TOKEN+TEAM_ID+PROJECT_ID) cloud providers. See [[claude-config-restore-2026-07]].
