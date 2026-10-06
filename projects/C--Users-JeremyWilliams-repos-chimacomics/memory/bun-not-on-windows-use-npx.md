---
name: bun-not-on-windows-use-npx
description: "chimacomics on Windows — bun 1.4.2 is now on PATH via scoop (verified 2026-10-06); plans still write npx commands, and the working copy has stale CRLF files."
metadata:
  node_type: memory
  type: project
  originSessionId: cd424894-0c15-448e-b9fc-ce449ac61baa
  modified: 2026-10-06T07:40:37.889Z
---

As of 2026-10-06 `bun` and `bunx` 1.4.2 resolve on Windows through scoop shims
(`~/scoop/shims/bun`), so the husky pre-commit hook (`bunx lint-staged`,
`bun run typecheck`, `bun run test`) runs natively. An earlier version of this
note said bun was absent; that is no longer true.

Plans and briefs for this repo still write the gates as `npx vitest run`,
`npx tsc --noEmit`, `npx eslint .`, `npx vite build`; both forms work.

Gotcha: `core.autocrlf=true` plus a pre-`.gitattributes` checkout leaves ~100
working-copy files with CRLF endings, so a local `npx eslint .` reports ~10k
`Delete ␍` prettier errors that CI never sees. `eslint --fix` rewrites them to
LF and `git diff` then shows only the real formatting changes (index is LF).

**Why:** a raw local lint count looked like a broken repo; the real CI failure on
2026-10-06 was 285 prettier errors in 16 files plus 4 rule errors.

**How to apply:** trust `git diff --stat` after `--fix`, not the raw local
count; keep `.github/workflows/ci.yml` on bun.
