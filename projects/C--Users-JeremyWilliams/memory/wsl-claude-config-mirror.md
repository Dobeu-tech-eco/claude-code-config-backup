---
name: wsl-claude-config-mirror
description: WSL Ubuntu 24.04 now has a mirrored Claude config; plus the Git-Bash→wsl.exe gotchas that make scripting it painful
metadata: 
  node_type: memory
  type: project
  originSessionId: b928ae6e-700b-43c0-af15-aa44cdbfa7a5
---

The WSL2 Ubuntu 24.04 distro (user `jeremyw`, `/home/jeremyw`) on this machine was given a mirror of the Windows `~/.claude` config on 2026-07-14. Setup: nvm + Node 22 (`~/.nvm`, default alias), `@anthropic-ai/claude-code` global, three stdio MCP servers re-registered under Linux npx (memory, sequential-thinking, Context7 — all Connected). Portable content (agents, commands, skills=377, rules, system-prompts, tools) is mirrored by **`~/.claude/sync-from-windows.sh`** (rsync from `/mnt/c/Users/JeremyWilliams/.claude`, all excludes anchored with leading `/` so they don't nuke same-named files inside skills). Windows = author, WSL = mirror; re-run the sync after Windows-side skill/agent edits. The 3 PowerShell hooks + statusline were ported to **bash + python3** (python3, not jq, to avoid a sudo apt install) at `~/.claude/hooks/*.sh` and `~/.claude/statusline.sh`; `settings.json`/`settings.local.json`/`CLAUDE.md` are WSL-specific (bash hook commands, `/home/jeremyw` paths) and excluded from the sync so they persist. WSL auth is separate from Windows (`.credentials.json` never copied). Plan file: `~/.claude/plans/quizzical-enchanting-hennessy.md`.

**Still requires the user (interactive, can't be automated):** run `claude` + `/login` in WSL for OAuth; the Composio plugin re-installs itself on first launch from the marketplace in settings.json.

**Git-Bash → wsl.exe scripting gotchas (these cost many retries — heed them):** The Claude Code `Bash` tool is Git Bash (MSYS2), and driving WSL through it has two independent traps. (1) **MSYS path conversion** rewrites POSIX args like `/usr/bin/bash` or `/home/jeremyw` into `C:/Program Files/Git/...` — prefix the whole command with `MSYS_NO_PATHCONV=1`. (2) **Inline shell variables get eaten**: a `$VAR` (or `VAR=x; ...$VAR`) written inside `wsl.exe -- bash -lc '...'` frequently expands to empty, and `$HOME` is often unset in that context. Reliable pattern: author a **self-contained script file** (with its own `export HOME=/home/jeremyw` and its own variables), write it with the Write tool to the scratchpad, then `sed 's/\r$//' /mnt/c/.../file > /tmp/file && bash /tmp/file` using **literal absolute paths only** in the inline command. Variables work fine *inside* the script file — only the inline `bash -lc` string mangles them. `/mnt/c` also has a brief write-visibility lag (a just-written file can read as 0 bytes for a moment).
