---
name: npm-package-publisher
description: Scaffolds and publishes Node.js npm packages to the public npm registry (registry.npmjs.org) and/or GitHub Packages (npm.pkg.github.com) via GitHub Actions release-triggered workflows. Use this whenever the user wants to publish, release, ship, or deploy an npm package, set up CI publishing, create a release-package.yml workflow, scope a package under an owner, configure .npmrc or publishConfig registry routing, wire NODE_AUTH_TOKEN, NPM_TOKEN, or GITHUB_TOKEN auth, add npm provenance or trusted publishing, or turn a repo into a publishable package — even if they only say npm, GitHub Packages, release a package, or CI publish. Do NOT use for installing or consuming packages, PyPI or other non-npm registries, Docker or container image publishing, or generic GitHub Actions workflows unrelated to package publishing.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: <package-name-or-scope> [--registry npm|gpr|both]
---

# npm Package Publisher

> Core philosophy: a package is "publishable" only when four things agree — the **name scope**, the **registry URL**, the **auth token**, and the **release trigger**. Break any one and `npm publish` fails (403, 404, or 409). Most failures are a mismatch between these four, not a code bug.

Publish Node.js packages to the public npm registry, to GitHub Packages, or to both, using a GitHub Actions workflow that fires on a GitHub Release.

## When to use / when not

Use for: setting up CI publishing, writing `release-package.yml`, choosing a registry, fixing a failing `npm publish`, scoping a package, configuring tokens/provenance, or scaffolding a brand-new publishable repo.

Do NOT use for: installing/consuming an already-published package (that is registry config on the install side, not publishing), non-npm registries (PyPI, crates, Maven), or container/image publishing.

## Step 0 — Detect state first

Before changing anything, read the current state. Never assume a clean repo.

```bash
test -f package.json && cat package.json || echo "NO package.json"
test -f package-lock.json && echo "lockfile OK" || echo "NO lockfile (npm ci will fail)"
ls .github/workflows/ 2>/dev/null
git remote -v 2>/dev/null
```

Branch on what exists: a fresh repo → scaffold (Path B). An existing package missing only CI → add the workflow + auth (Path A, steps 3–7).

## Decision — which registry

Confirm the target with the user if ambiguous. The choice changes the package **name**, the **registry URL**, and the **token**.

| | Public npm | GitHub Packages (GPR) | Both |
|---|---|---|---|
| Name requirement | Any (`pkg` or `@scope/pkg`) | MUST be `@owner/pkg`, owner **lowercase** | MUST be `@owner/pkg` |
| Registry URL | `https://registry.npmjs.org` | `https://npm.pkg.github.com` | per-job (see below) |
| Auth token (`NODE_AUTH_TOKEN`) | `secrets.NPM_TOKEN` (you create it) | `secrets.GITHUB_TOKEN` (built-in) | both, one per job |
| Workflow permissions | `id-token: write` (provenance) | `packages: write`, `contents: read` | union of both |
| Scoped-public note | needs `--access public` | n/a | needs `--access public` |
| `repository` field in package.json | optional | **required** to link package↔repo | required |

Registry-routing rule (the #1 footgun): do **not** hardcode a committed `.npmrc` registry when targeting Both — it pins every publish to one registry. Instead let each job's `actions/setup-node` write its own job-local `.npmrc` via `registry-url`, and leave `publishConfig.registry` **unset**. Use `publishConfig` only for single-registry packages. See [references/auth-and-registry.md](references/auth-and-registry.md).

## Path A — Add publishing to an existing package

1. **Confirm the name matches the target** (table above). For GPR/Both, rename to `@owner/pkg` (lowercase owner) and add a `repository` field. Edit `package.json`, do not hand-wave it.
2. **Set the test script** so CI's `npm test` does not fail an unconfigured repo: `"test": "exit 0"` until real tests exist.
3. **Copy the matching workflow** into `.github/workflows/release-package.yml`:
   - npm → [assets/release-package-npm.yml](assets/release-package-npm.yml)
   - GPR → [assets/release-package-gpr.yml](assets/release-package-gpr.yml)
   - both → [assets/release-package-dual.yml](assets/release-package-dual.yml)
   Adjust `node-version` to match the project (default 20; 22 LTS is also fine).
4. **Configure routing** in `package.json`:
   - npm single, scoped → `"publishConfig": { "access": "public", "provenance": true }`
   - GPR single → `"publishConfig": { "@owner:registry": "https://npm.pkg.github.com" }`
   - Both → omit `publishConfig.registry`; per-job `registry-url` handles it.
5. **Configure auth:**
   - GPR uses the built-in `GITHUB_TOKEN` — no secret to create; just keep `permissions: packages: write` in the job.
   - npm needs a repo secret `NPM_TOKEN` (a granular or automation access token from npmjs.com). Trusted Publishing via OIDC is the token-free alternative — see [references/auth-and-registry.md](references/auth-and-registry.md).
6. **Generate the lockfile and commit** (the workflow runs `npm ci`, which *requires* a committed lockfile):
   ```bash
   npm install
   git add package.json package-lock.json .github/workflows/release-package.yml
   git commit -m "ci: publish on release"
   git push
   ```
7. **Trigger by creating a GitHub Release** (tag like `v1.0.0`). The workflow runs `build` then the publish job(s).
8. **Verify** — repo → right sidebar → **Packages**, or `npm view @owner/pkg version`. On failure, go to [references/troubleshooting.md](references/troubleshooting.md).

Bump the `version` in `package.json` before every release — republishing an existing version is rejected (409). This is the single most common CI failure.

## Path B — Scaffold a new publishable repo

Run the deterministic scaffolder instead of hand-creating files:

```bash
python scripts/scaffold_package.py "@owner/my-lib" --registry both --owner owner --dir ./my-lib
```

Flags: `--registry npm|gpr|both` (default both), `--owner <github-owner>` (lowercase; required for gpr/both unless the name is already scoped), `--node-version 20`, `--no-provenance`, `--description "..."`, `--dir <path>`.

It writes `index.js`, a correct `package.json` (name, `repository`, `files`, test=`exit 0`, registry-appropriate `publishConfig`), `.gitignore`, `README.md`, and the matching `.github/workflows/release-package.yml`. It does **not** run `npm install` or `git push` — it prints those as the next manual steps so the user controls the lockfile and the first commit.

## Verify checklist

- [ ] `package.json` name valid for the target registry (GPR → `@owner/pkg`, lowercase)
- [ ] `package-lock.json` committed (else `npm ci` fails)
- [ ] Workflow job has the right `permissions` and `NODE_AUTH_TOKEN`
- [ ] `version` bumped since the last publish
- [ ] For npm scoped-public: `--access public` present
- [ ] For GPR: `repository` field set

## Skill files

```
npm-package-publisher/
├── SKILL.md
├── scripts/
│   └── scaffold_package.py          # Path B scaffolder
├── references/
│   ├── auth-and-registry.md         # tokens, .npmrc vs publishConfig, OIDC/provenance, consumer install
│   ├── workflows.md                 # triggers, the 3 templates, customization
│   └── troubleshooting.md           # failure → cause → fix
└── assets/
    ├── release-package-npm.yml      # public npm only
    ├── release-package-gpr.yml      # GitHub Packages only
    ├── release-package-dual.yml     # both registries
    └── package.json.template        # annotated starter
```
