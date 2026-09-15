---
name: routeready-design-system-sync
description: RouteReady syncs its components to Claude Design project 8be0c06f-b2f1-4459-af8e-9b799dd1ee13; the repo is an app, not a DS package, so design-sync needs two declared lib forks
metadata:
  type: project
---

RouteReady's design system lives at `https://claude.ai/design/p/8be0c06f-b2f1-4459-af8e-9b799dd1ee13`
("RouteReady Design System", first synced 2026-09-15). 286 components.

The non-obvious part: RouteReady is a **Vite app, not a published design-system package** — no
library `dist/`, no shipped `.d.ts`. Plain `/design-sync` cannot handle that shape. The working
setup needs a generated barrel (`--entry .design-sync/ds-entry.tsx`) plus two *declared* forks in
`.design-sync/overrides/` (`dts.mjs` so prop contracts resolve from `src/*.tsx` instead of every
component degrading to `[key: string]: unknown`; `source-kit.mjs` so the 240 `src/components/ui`
exports do not collapse into one `general` group).

**Before changing anything here, read `.design-sync/NOTES.md` in the repo** — it carries the full
build recipe, the CSS snapshot step, the triaged render warns, and the re-sync risk list.

Related: [[no-worktrees-routeready]], [[routeready-bun-authored-node-modules]]
