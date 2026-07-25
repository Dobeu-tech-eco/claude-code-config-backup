# Publish `@dobeu` Design System to Figma's Private npm Registry — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure this Turborepo monorepo so `@dobeu-private/tokens` and `@dobeu-private/components-react` build cleanly and publish to Figma's private npm registry via `pnpm publish-packages`.

**Architecture:** pnpm workspace + Turbo + Changesets. Two source-complete packages exist (`packages/tokens`, `packages/components-react`). The repo was never wired for publishing: packages are `private`, there is no `.npmrc`, changesets targets public npm, and the `tsc` output paths don't match the `package.json` entry points. This plan fixes those and points publishing at Figma's registry.

**Tech Stack:** pnpm@10.33.2, Turbo 2, TypeScript 5.9, Changesets, `@figma/code-connect`, Figma private npm registry.

## Context

**Why:** The design system needs to be consumable by Figma (Code Connect / Make kits), which requires publishing the packages to Figma's private npm registry. The repo is currently a working monorepo but was "not constructed for" publishing.

**The scope decision (important):** Figma issued a registry credential mapping the **`@dobeu-private`** scope, but the entire repo uses **`@dobeu/*`**. Publishing `@dobeu/*` with a token registered for `@dobeu-private` will 403. Chosen resolution (user delegated the choice): **rename the npm scope repo-wide `@dobeu/` → `@dobeu-private/`** so it matches the token you already have — no external Figma-admin scope registration required. Trade-off to be aware of: downstream React apps in `dobeu-eco` that were meant to consume `@dobeu/components-react` will need the new name **and** `.npmrc` auth to Figma's registry. That downstream ripple is out of scope here; this plan gets the packages published.

**Automation scope (user delegated):** Local manual publish only. The target GitHub repo/remote is still TBD, so no CI workflow is added. Adding a `.github/workflows` changesets-publish job is documented as a follow-up, not built.

**Security:** The auth token was pasted into the chat — **rotate it in Figma before real use.** The committed `.npmrc` uses `${FIGMA_NPM_TOKEN}` env interpolation; the literal token is never committed.

## Global Constraints

- Package manager: **pnpm@10.33.2** (`packageManager` pin). Node >= per `tsconfig.base` ES2022.
- Registry URL (verbatim): `https://registry.figma.com/npm/ab968257-ad2f-462c-83e8-8cded2c9a6c4/registry/`
- Scope after rename: `@dobeu-private` (private registry → `access: restricted`).
- Never commit the auth token. `.npmrc` references `${FIGMA_NPM_TOKEN}` only.
- Rename target string is exactly `@dobeu/` (with the slash) — this does NOT touch `--dobeu-`, Tailwind `dobeu.*`, `DobeuButton`, or the `dobeu` wordmark.
- Shell is PowerShell 7 (`pwsh`) on Windows.

---

## Task 1: Rename the npm scope `@dobeu/` → `@dobeu-private/`

**Files (every occurrence of the literal `@dobeu/`):**
- Modify: `packages/tokens/package.json` (`name`)
- Modify: `packages/components-react/package.json` (`name`, `peerDependencies` key)
- Modify: `.changeset/foundation-tokens-and-react.md`, `.changeset/foundation-components-react.md`
- Modify (docs/consistency): `README.md`, `CLAUDE.md`, `docs/changeset-policy.md`, `docs/component-parity-checklist.md`, `docs/design-to-code-workflow.md`, `docs/figma-pro-library-setup.md`, `docs/token-contract.md`, `packages/components-react/figma/code-connect-urls.ts`

**Interfaces:**
- Produces: package names `@dobeu-private/tokens`, `@dobeu-private/components-react`; peer dep key `@dobeu-private/tokens` (value stays `workspace:*`).

- [ ] **Step 1: Global find/replace** the exact string `@dobeu/` with `@dobeu-private/` across the whole repo. Verify with `grep` that zero `@dobeu/` remain and that `--dobeu-`, `dobeu.`, and `Dobeu` identifiers are untouched.
- [ ] **Step 2: Sanity-read** `packages/components-react/package.json` — confirm `name` is `@dobeu-private/components-react` and `peerDependencies` has `"@dobeu-private/tokens": "workspace:*"`.
- [ ] **Step 3: Commit** — `chore: rename npm scope to @dobeu-private for Figma registry`.

---

## Task 2: Add `.npmrc` pointing the scope at Figma's registry

**Files:**
- Create: `.npmrc` (repo root)

- [ ] **Step 1: Create `.npmrc`** (committable — no literal secret):

```ini
@dobeu-private:registry=https://registry.figma.com/npm/ab968257-ad2f-462c-83e8-8cded2c9a6c4/registry/
//registry.figma.com/npm/ab968257-ad2f-462c-83e8-8cded2c9a6c4/registry/:_authToken=${FIGMA_NPM_TOKEN}
```

- [ ] **Step 2: Verify** `.npmrc` is NOT ignored (`.gitignore` ignores `.env*`, not `.npmrc`) so the sanitized config is tracked, but confirm no literal token is present.
- [ ] **Step 3: Commit** — `chore: add .npmrc for Figma private registry (token via env)`.

---

## Task 3: Make both packages publishable

**Files:**
- Modify: `packages/tokens/package.json`, `packages/components-react/package.json`
- Modify: `.changeset/config.json`

**Interfaces:**
- Produces: both packages publishable to the Figma registry with `access: restricted`.

- [ ] **Step 1:** In each package `package.json`, remove `"private": true` and add:

```json
"publishConfig": {
  "registry": "https://registry.figma.com/npm/ab968257-ad2f-462c-83e8-8cded2c9a6c4/registry/",
  "access": "restricted"
}
```

- [ ] **Step 2:** In `.changeset/config.json`, change `"access": "public"` → `"access": "restricted"`.
- [ ] **Step 3: Commit** — `chore: make @dobeu-private packages publishable to Figma registry`.

---

## Task 4: Fix `tsc` output paths so entry points resolve

**Problem:** Both packages compile with `rootDir: "."` + `include: ["src","test",...]`, so `tsc` emits `dist/src/index.js` and `dist/test/**`, but `package.json` `main`/`types` point at `dist/index.js`. components-react's `exports` import already points at `dist/src/index.js` (inconsistent with its own `main`). This must be reconciled or the published package won't resolve and will ship test files.

**Chosen fix:** give each package a dedicated build tsconfig that emits from `src` only (clean `dist/index.js`), keep the existing tsconfig for typecheck.

**Files:**
- Create: `packages/tokens/tsconfig.build.json`, `packages/components-react/tsconfig.build.json`
- Modify: `packages/tokens/package.json` (`build` script), `packages/components-react/package.json` (`build` script + `exports` import path)

- [ ] **Step 1:** Create `packages/tokens/tsconfig.build.json`:

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": { "rootDir": "src" },
  "include": ["src"],
  "exclude": ["test", "**/*.test.*"]
}
```

- [ ] **Step 2:** Create `packages/components-react/tsconfig.build.json`:

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": { "rootDir": "src" },
  "include": ["src"],
  "exclude": ["test", "**/*.test.*", "figma"]
}
```

- [ ] **Step 3:** Point each `build` script at the build config:
  - tokens: `"build": "node ./scripts/build.mjs && tsc -p tsconfig.build.json"`
  - components-react: `"build": "tsc -p tsconfig.build.json"`

- [ ] **Step 4:** In `packages/components-react/package.json`, change the `exports["."].import` from `./dist/src/index.js` to `./dist/index.js` (now that `rootDir: src` emits `dist/index.js`). Confirm `main`/`types` (`./dist/index.js`, `./dist/index.d.ts`) now match. tokens `main`/`types`/subpath exports already match (`dist/index.js`, `dist/css/...` from `build.mjs`).

- [ ] **Step 5: Build and inspect** — `pnpm install` then `pnpm build`; then `Get-ChildItem -Recurse packages\tokens\dist`, `...\components-react\dist`. Confirm `dist/index.js` + `dist/index.d.ts` exist at the paths the `package.json` fields name, and that **no `dist/test/**` was emitted**. Fix any remaining path mismatch to match reality.
- [ ] **Step 6: Commit** — `fix: emit clean package entry points from src only`.

---

## Task 5: Version, dry-run, and publish

**Files:**
- Modify (by tooling): package versions + `CHANGELOG.md` (generated by `changeset version`), `.changeset/*.md` consumed.

- [ ] **Step 1: Set the token** (rotate first) — `pwsh`: `$env:FIGMA_NPM_TOKEN = "<new-token>"`.
- [ ] **Step 2: Apply changesets** — `pnpm changeset version` (consumes the two pending changesets, bumps 0.1.0 → 0.1.1, writes CHANGELOGs). Review the diff.
- [ ] **Step 3: Build** — `pnpm build`. Confirm green.
- [ ] **Step 4: Dry-run publish per package** to validate auth + tarball without pushing:
  - `pnpm --filter @dobeu-private/tokens publish --dry-run --no-git-checks`
  - `pnpm --filter @dobeu-private/components-react publish --dry-run --no-git-checks`
  - Confirm each prints the Figma registry URL, the `@dobeu-private/*` name, and a tarball containing `dist/` (+ `figma/` for components-react), and that `workspace:*` is rewritten to a real version.
- [ ] **Step 5: Publish for real** — `pnpm publish-packages` (`turbo build && changeset publish`). tokens publishes before components-react (dependency order).
- [ ] **Step 6: Commit** the version bump — `chore: release @dobeu-private packages`.

---

## Verification (end-to-end)

1. **Auth/build:** `$env:FIGMA_NPM_TOKEN` set → `pnpm install` → `pnpm build` succeeds.
2. **Layout:** `dist/index.js` + `dist/index.d.ts` exist per package; tokens also has `dist/css/variables.css`, `dist/tailwind/tokens.json`, `dist/framer/tokens.json`, `dist/webflow/tokens.json`; no `dist/test/**`.
3. **Tarball:** `pnpm --filter @dobeu-private/tokens publish --dry-run --no-git-checks` (and components-react) show the Figma registry, correct scoped name, and expected files.
4. **Published:** after real publish, confirm resolution:
   - `npm view @dobeu-private/tokens version --registry https://registry.figma.com/npm/ab968257-ad2f-462c-83e8-8cded2c9a6c4/registry/`
   - Repeat for `@dobeu-private/components-react`; and check the package appears in Figma's registry UI.
5. **No secret leaked:** `git grep` for the token string returns nothing; `.npmrc` contains only `${FIGMA_NPM_TOKEN}`.

**Known out-of-scope (note, don't silently skip):**
- Component **tests** need `react`, `react-dom`, `@testing-library/react` added as devDeps — currently absent, so `pnpm test` for components-react will fail. Publishing (`turbo build`) does not run tests, so this does not block publish, but flag it.
- CI publish (`.github/workflows`) is not added — future follow-up once the GitHub repo + `FIGMA_NPM_TOKEN` secret exist.
- Downstream `@dobeu/*` → `@dobeu-private/*` consumer updates in other repos.
