---
name: origin-is-wenlan-windows-install
description: "The \"origin\" Claude Code plugin's CLI/daemon was renamed upstream to wenlan; installed natively on this Windows box 2026-09-14 (~\\.wenlan\\bin, scheduled task, user-scope MCP)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 42221ac8-ec10-4a24-bbd6-7280c44cfa3a
  modified: 2026-09-14T17:16:24.984Z
---

The `origin@buildwithclaude` plugin (v0.6.1, `~\.claude\plugins\cache\buildwithclaude\origin\0.6.1`) is
stale and macOS-only: its `install.sh`, `/origin:init` skill, and `npx origin-mcp` runner all die on Windows.
Upstream renamed the project to **wenlan** (`github.com/7xuanlu/wenlan`; `origin-mcp` npm is deprecated →
`wenlan-mcp`). The `wenlan` npm wrapper is *also* darwin-arm64-only, but the GitHub release ships
`wenlan-windows-x64.zip` with native exes.

Installed on 2026-09-14:
- Binaries: `C:\Users\JeremyWilliams\.wenlan\bin\{wenlan,wenlan-server,wenlan-mcp}.exe` (v0.18.7, sha256 of zip
  verified against release `SHA256SUMS`). On user PATH.
- Daemon: Windows scheduled task `WenlanServer` → `http://127.0.0.1:7878/api/health`. Data root
  `%LOCALAPPDATA%\wenlan`. Local-memory mode (no model, no API key). Manage with `wenlan background on|off`,
  `wenlan restart`, `wenlan status`, `wenlan doctor`, `wenlan lint`.
- MCP: user-scope server `wenlan` → `wenlan-mcp.exe --agent-name claude-code` (`claude mcp get wenlan`;
  remove with `claude mcp remove wenlan -s user`). Tools: capture / recall / context / doctor.
- Upgrade path: re-download the newer `wenlan-windows-x64.zip` into `~\.wenlan\bin`, then `wenlan restart`.
  The plugin hook's "upgrade" one-liner (`curl … install.sh | bash`) will not work here.

**Why:** the plugin's SessionStart hook prints "[origin] daemon not running. Run /origin:init" until something
answers on 7878; `/origin:init` cannot succeed on Windows. Also note the cached `hooks/check-daemon.sh` has two
junk bytes (` d`) before its shebang — bash tolerates it, harmless.

**How to apply:** treat `origin` and `wenlan` as the same thing. Don't run `/origin:init` or the bash installer;
use `wenlan …` directly. If the plugin ever ships a `wenlan` plugin, swap `origin` for it.

Related: [[windows-node-is-scoop-nodejs-lts]]
