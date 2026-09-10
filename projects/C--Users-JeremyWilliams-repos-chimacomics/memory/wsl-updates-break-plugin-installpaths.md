---
name: wsl-updates-break-plugin-installpaths
description: Updating a Claude Code plugin from WSL writes a /mnt/c POSIX installPath that makes the plugin silently fail to load in Windows sessions.
metadata: 
  node_type: memory
  type: reference
  originSessionId: 378102ce-4568-4bf0-87f5-1f56002e2d41
  modified: 2026-09-10T09:50:40.323Z
---

`~/.claude/plugins/installed_plugins.json` stores an absolute `installPath` per plugin. Updating a plugin from a **WSL** session writes it in POSIX form (`/mnt/c/Users/...`); a **Windows** session cannot resolve that, so the plugin loads nothing — no skills, no agents, no commands — with **no error message**. Enablement in `settings.json` still shows `true`, which makes it look fine.

Symptom: the plugin's skills/agents are simply absent from the session registry.

Diagnose:
```bash
grep -n '"installPath": "/mnt' ~/.claude/plugins/installed_plugins.json
```
Any hit is broken. Fix by rewriting that one value to the `C:\Users\...` form (back the file up first; it is one JSON object, so patch with python rather than sed).

Hit on 2026-09-10 for `oh-my-claudecode@omc` 5.3.0 — 1 of 108 entries was POSIX, and OMC had silently stopped loading. Same WSL/Windows split that causes [[bun-not-on-windows-use-npx]].
