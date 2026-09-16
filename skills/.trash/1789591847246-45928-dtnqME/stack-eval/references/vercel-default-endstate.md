# Vercel-oriented production default (when user gives no end-state)

Use this when P0 receives no guidance. Adapt names to the active monorepo; defaults below match **Design System Weaver** (`dobeutech-designsystem-weaver`).

## Target

Ship a **Vercel-oriented production** posture:

- **SPAs:** `@workspace/design-forge` (primary UI) and optionally `@workspace/mockup-sandbox` as Vite apps suitable for Vercel static/SPA hosting (preview + production).
- **API:** `@workspace/api-server` (Express) reachable for preview/prod — either as a Vercel-compatible serverless/edge adaptation **or** a documented companion host with env parity. Prefer a path that supports Vercel preview URLs for the SPA and a stable API base URL contract.
- **Data:** Postgres via `DATABASE_URL`; schema via `pnpm --filter @workspace/db run push` (dev) with a documented prod migration story.
- **AI:** `AI_INTEGRATIONS_OPENAI_API_KEY` + `AI_INTEGRATIONS_OPENAI_BASE_URL` present; import may need a real/stub endpoint; generate/download may fall back deterministically.

## Quality gates

- `pnpm run typecheck` must pass.
- `pnpm run build` must pass for packages in the deploy surface.
- **eslint:** N/A → typecheck is the lint substitute.
- **tests:** N/A until a runner is added; document N/A in completion gates.

## Env contract (minimum)

| Var | Notes |
|-----|--------|
| `PORT` | API (local 5000; prod as platform requires) |
| `DATABASE_URL` | Postgres |
| `AI_INTEGRATIONS_OPENAI_API_KEY` | Non-empty to boot |
| `AI_INTEGRATIONS_OPENAI_BASE_URL` | OpenAI-compatible base |

SPA proxies `/api` → API in local dev; production must document the public API origin.

## Git / remotes

- Prefer existing **GitHub** `origin`; verify push.
- Backup remotes only after GitHub verification (see P6).

## Success criteria

1. Preview deploy path documented and runnable for the main SPA.
2. Typecheck + build green on the execution branch.
3. Env checklist complete; no secrets in git.
4. Master plan executed with all P0/P1 gaps closed or explicitly deferred.
5. `.agent/` ledger shows subtasks with `passes=true` only after completion gates.

## Tag

`end_state: vercel-default`
