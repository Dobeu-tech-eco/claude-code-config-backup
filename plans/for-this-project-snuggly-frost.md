# Build & Fix — dobeu.net (ecc-on-dobeu worktree)

## Context

`/ecc:build-fix` was run against this worktree. The first diagnostic (`pnpm type-check`)
returned a single error:

```
app/layout.tsx(7,8): error TS2882: Cannot find module or type declarations for
  side-effect import of './globals.css'.
 WARN  Local package.json exists, but node_modules missing, did you mean to install?
```

**Root cause: dependencies are not installed** — `node_modules/` is absent in this
worktree. The `globals.css` error is purely a symptom (tsc can't resolve modules or
CSS-module ambient types without the installed toolchain). There are **no confirmed
source-level build errors** yet; none can be diagnosed until install completes.

`pnpm-lock.yaml` is present (~282 KB), so a `--frozen-lockfile` install is the correct,
reproducible path (matches CI in `.github/workflows/ci.yml`).

## Plan

### Step 1 — Install dependencies
```bash
pnpm install --frozen-lockfile
```
Run in background (long-running). This is the actual blocker — likely the whole fix.

### Step 2 — Re-run the full verifier
```bash
pnpm verify   # type-check && lint && test:ci && build:strict
```
`pnpm verify` mirrors CI and is the project's real build gate (`next.config.ts` has
`ignoreBuildErrors: false` + `ignoreDuringBuilds: false`). Capture output per stage so
failures are attributable (type-check vs lint vs test vs strict-build).

If `pnpm verify` fails at the strict-build stage on a warning rather than a genuine
error, fall back to plain `pnpm build` to confirm Vercel-parity behavior before treating
it as a real failure.

### Step 3 — Fix loop (only if real errors surface)
For each genuine error, one at a time (per `/ecc:build-fix` protocol):
1. Read ~10 lines of context around the error.
2. Diagnose root cause (missing import, type mismatch, lint rule).
3. Apply the **smallest** Edit that resolves it — no refactors, no architectural change.
4. Re-run the failing stage to confirm the error is gone and none introduced.

### Guardrails (stop and ask)
- A fix introduces more errors than it resolves.
- Same error persists after 3 attempts.
- A fix would require an architectural change (out of scope for build-fix).
- Expected: **install alone makes the tree green** — if so, report that and stop.

## Verification
- `pnpm verify` exits 0 (type-check + lint + test:ci + strict build all pass).
- Report: errors fixed (with paths), errors remaining, new errors introduced (target: 0).
- No source edits at all is the most likely and best outcome — the "error" was an
  uninstalled worktree, not broken code.

## Files
- No source files are expected to change. `app/layout.tsx` is only implicated as a
  symptom; it will not need edits unless a real error survives install.
