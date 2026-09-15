---
name: notion-cli-windows-npm-only
description: Notion CLI (ntn) must be installed on Windows via npm; the ntn.dev bash installer hard-refuses Windows
metadata:
  type: reference
---

`curl -fsSL https://ntn.dev | bash` does NOT work on this machine. The installer
detects `MINGW*|MSYS*|CYGWIN*` and exits with
"This installer does not support Windows. Install via npm: npm install -g ntn".

Correct install: `npm install -g ntn` (installed 2026-09-14, v0.23.5).
Lands as `ntn.exe` shim in the scoop Node bin dir — see [[windows-node-is-scoop-nodejs-lts]].
npm 11 warns the `preinstall` script was blocked, but the CLI still works; the
warning is not a failure. Config lives at `%APPDATA%\notion`.
`ntn doctor` reports setup health; `ntn login` is interactive OAuth (run it yourself).
