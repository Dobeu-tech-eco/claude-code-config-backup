---
name: bun-not-on-windows-use-npx
description: chimacomics CLAUDE.md says to use bun, but bun is not installed on this Windows machine — run the gates with npx instead.
metadata:
  type: project
---

`chimacomics/CLAUDE.md` documents every command as `bun run ...`, but there is no
`bun` on this Windows host (no `bun.exe` under `~/.bun`, `%LOCALAPPDATA%`, or
`C:\Program Files`; not on PATH in either PowerShell or the Bash tool). Earlier
work on this repo ran under WSL at `/home/jeremyw/work/chimacomics`, which is
where bun lives.

`node_modules` is present and current, so run the gates directly on Windows:

- `npx vitest run` (not `--reporter=basic`; that reporter was removed in vitest 3+)
- `npx tsc --noEmit`
- `npx eslint .` / `npx eslint . --fix`
- `npx vite build`

**Why:** reaching for `bun run test` on Windows fails with "command not found"
and reads like a broken repo when the toolchain is actually fine.

**How to apply:** on Windows, substitute the `npx` equivalents above; only use
the documented `bun` commands from WSL. Keep `.github/workflows/ci.yml` on bun —
CI runs on ubuntu with `oven-sh/setup-bun`.
