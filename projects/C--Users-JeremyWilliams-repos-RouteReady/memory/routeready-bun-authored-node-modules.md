---
name: routeready-bun-authored-node-modules
description: RouteReady node_modules is bun-authored and npm cannot repair it; bun.lock pins 34 packages to Lovable's GCP Artifact Registry
metadata:
  type: project
---

RouteReady's `node_modules` is installed by **bun**, not npm. It has no
`node_modules/.package-lock.json` (npm always writes one), so npm's arborist
cannot reason about the tree: any `npm install` fails with
`Cannot read properties of null (reading 'edgesOut')`. Use `bun install`.
`bun` is NOT installed on this Windows machine as of 2026-09-14, so
`npm run dev` / `npm run build` cannot run at all — `predev`/`prebuild` call
`bunx tsx scripts/generate-sitemap.ts`.

Installed tree is incomplete: 216 top-level dirs against 419 `bun.lock`
entries. The genuinely missing set is small — the `react-helmet-async@3.0.0`
subtree (`invariant`, `react-fast-compare`, `shallowequal`) plus
`lightningcss-win32-x64-msvc` (Tailwind 4 needs it on this platform). The
other absentees are correctly-skipped foreign-platform optional binaries
(`fsevents`, other `lightningcss-*`). The missing helmet subtree is why
`tsc --noEmit` reports `Cannot find module 'react-helmet-async'` in
`src/components/route-head.tsx` and `src/main.tsx` — a stale install, not a
type error and not an unsatisfiable range (3.0.0 is real and is npm `latest`).

**`bun.lock` pins 34 packages to Lovable's private GCP Artifact Registry**
(`europe-west4-npm.pkg.dev` / `europe-west1-npm.pkg.dev`,
`lovable-core-prod/sandbox-npm-cache`) rather than the public npm registry —
including load-bearing ones: `@supabase/supabase-js`, `react-router-dom`,
`react-i18next`, `react-helmet-async`, and all `@amplitude/*` plugins. That
registry IS publicly reachable (verified HTTP 200 on a tarball fetch), so
`bun install` works from here, but the supply chain runs through Lovable
infrastructure — relevant to any production/vendor review.

Do not "fix" this with `npm install`: it would create `package-lock.json`
alongside `bun.lock`, violating the dual-lockfile onboarding gate in
`repos/CLAUDE.md`. `package.json` has no `packageManager` field pinned.
Related: [[windows-node-is-scoop-nodejs-lts]] (npm scripts can't resolve
`node_modules/.bin`; invoke `./node_modules/.bin/<tool>` directly).
