---
name: windows-node-is-scoop-nodejs-lts
description: "Node on this Windows box is scoop nodejs-lts (24.x); its PATH entries silently vanished once and were restored with `scoop reset nodejs-lts` on 2026-09-14"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 42221ac8-ec10-4a24-bbd6-7280c44cfa3a
  modified: 2026-09-14T17:16:35.352Z
---

Windows-side Node is **scoop** `nodejs-lts` (24.21.0 as of 2026-09-14) at
`C:\Users\JeremyWilliams\scoop\apps\nodejs-lts\current` (+ `\bin` for npm globals; global prefix is
`scoop\persist\nodejs-lts\bin`). It is *not* the winget `OpenJS.NodeJS.LTS` entry (that shows in `winget list`
but has no `node.exe` on disk) and not `C:\Program Files\nodejs`. WSL has its own nvm Node 22.

Scoop wires node via `env_add_path` (user PATH), not shims — so if the user PATH gets rewritten, `node`/`npm`
disappear from every shell while the files stay put. Fix: `scoop reset nodejs-lts` (re-adds both PATH entries,
non-destructive). Happened once; fixed 2026-09-14.

**How to apply:** when `node: command not found` in a Claude tool shell, check
`[Environment]::GetEnvironmentVariable("PATH","User")` for `scoop\apps\nodejs-lts\current` before assuming
Node isn't installed. Git Bash and non-interactive pwsh only see what's in the registry PATH at spawn time.

Related: [[origin-is-wenlan-windows-install]]
