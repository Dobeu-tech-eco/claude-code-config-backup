---
name: windows-uv-venv-lib64-repair
description: An interrupted uv sync on this Windows box leaves a dangling .venv/lib64 reparse point that blocks every later uv run; how to repair it.
metadata:
  type: project
---

On this Windows 11 machine, an interrupted `uv sync` in `repos/si-agent-core` can leave `.venv`
gutted except for `pyvenv.cfg` and a dangling `lib64` directory reparse point pointing at a
`lib` that no longer exists. Every subsequent `uv run` (even with `--no-sync`) then fails with:

    error: failed to remove file `\?\...\.venv\lib64`: Access is denied. (os error 5)

Windows refuses to remove the reparse point through `rm`. Repair with PowerShell, which deletes
the link without following it, then rebuild:

    (Get-Item "<repo>\.venv\lib64" -Force).Delete()
    uv sync --frozen

Confirmed and used 2026-09-24. Inspect first with `Get-Item -Force` — `Attributes` should read
`Directory, ReparsePoint` and the target should not exist; only then is deleting safe.
Related: [[si-agent-core-ci-gates]]
