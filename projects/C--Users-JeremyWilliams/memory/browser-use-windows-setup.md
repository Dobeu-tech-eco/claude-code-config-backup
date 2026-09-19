---
name: browser-use-windows-setup
description: "browser-use/browser-harness install + skill registration on Windows — the `skill install` self-upgrade bug and how Chrome must be launched manually"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82df3ea0-b4b1-4b24-8d47-b67ced674d56
  modified: 2026-09-19T20:25:21.193Z
---

Installed via `uv tool install browser-use --python 3.12` (pulls in `browser-harness` 0.1.13,
which actually provides the `browser-use`/`bu`/`browseruse`/`browser` CLI entry points).

**`browser-use skill install` is broken on this Windows machine — never run it.** It shells out
to `uv tool install --python 3.12 --upgrade --force browser-use` as a side effect. On Windows
this self-locks: the running `browser-use.exe` process is loaded from
`AppData\Roaming\uv\tools\browser-use\Scripts\`, and uv can't delete that directory while it's
in use (`Access is denied (os error 5)`). uv partially tears down the venv before hitting the
lock, leaving `ModuleNotFoundError: No module named 'browser_use'` — every subsequent CLI call
fails until you `uv tool uninstall browser-use` + reinstall clean.

**Workaround:** use `browser-use skill show > <path>\SKILL.md` instead — it only prints the
skill text and does not trigger the force-reinstall. Skill lives at
`~/.claude/skills/browser-harness/SKILL.md` (registered under name `browser-harness`, not
`browser-use`).

**Connecting to a browser:** the SKILL.md claims Chrome auto-launches if not running, but on
this machine (a background job / non-interactive session) it does not — `browser-use` fails
with `chrome-not-running` in
`C:\Users\JeremyWilliams\.config\browser-harness\tmp\bu-default.log`. Fix: launch Chrome
manually first, then the daemon attaches fine, e.g.:
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList `
  "--remote-debugging-port=9222","--user-data-dir=`"$env:LOCALAPPDATA\browser-harness-profile`"","--no-first-run","--no-default-browser-check"
```
Verify with `curl http://localhost:9222/json/version` before retrying `browser-use`.
`browser-use doctor` should then show chrome running / daemon alive / active browser
connections ≥1.

**How to apply:** if browser-use CLI calls start failing with `ModuleNotFoundError:
No module named 'browser_use'`, it's this self-lock bug — don't debug further, just
`uv tool uninstall browser-use && uv tool install browser-use --python 3.12`. Never re-run
`skill install`; use `skill show` for any future re-registration.
