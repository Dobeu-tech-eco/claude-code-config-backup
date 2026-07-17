# Integration cookbook — concrete recipes per app

Specific, opinionated recipes for the eight integrations that show up in nearly every full-stack build. For each: the canonical setup, the things that go wrong, and the verification you can run before claiming a feature green.

These recipes assume Composio for cross-system orchestration. Where a native MCP exists for the same app and is connected, prefer it for that app's actions; come back to Composio for the multi-app coordination.

---

## GitHub

### Initial setup (Phase 2, F001-ish)

1. `GITHUB_CREATE_REPOSITORY` — name = `<idea-slug>`, private = true (default), auto_init = true, gitignore_template = `Node` (or relevant).
2. Locally: `gh repo clone <user>/<idea-slug>` or set the remote on an existing scaffolded directory.
3. `GITHUB_CREATE_BRANCH_PROTECTION_RULE` for `main`: require PRs, require status checks (lint, test, build).

### Things that go wrong

- **Branch protection blocks the agent.** If the rule requires reviews, the agent (alone) cannot merge. Mitigation: have the user add the agent's GitHub identity to the bypass list, or work on `main` directly during MVP and add protection in Phase 4.
- **Default branch is `master`.** Newer repos default to `main`; if the user has `master` set in their personal defaults, the agent's reference to `main` will fail. Always read the default branch from the repo metadata first.
- **Force push blocked.** Don't try. Revert the bad commit and push forward.

### Verification

```bash
gh repo view <user>/<idea-slug> --json defaultBranchRef,visibility,url
```

---

## Linear

### Initial setup

1. Get the team ID once at session start: `LINEAR_LIST_TEAMS`. Cache in `state.json`.
2. `LINEAR_CREATE_PROJECT` — name = `<idea-slug>`, team_id = cached.
3. Optionally `LINEAR_CREATE_CYCLE` for "MVP sprint."

### Pattern: feature → Linear issue mapping

Each feature in `tasks.json` gets a Linear issue created on transition to `in_progress`, updated when status changes, closed when `passes: true`. This gives the user a real-time view of progress in their PM tool.

```json
COMPOSIO_MULTI_EXECUTE_TOOL [
  { "tool": "LINEAR_CREATE_ISSUE", "params": {"title": "F001 Initialize Next.js", "team_id": "...", "project_id": "..."}},
  { "tool": "LINEAR_CREATE_ISSUE", "params": {"title": "F002 CI/CD basics", "team_id": "...", "project_id": "..."}}
  // ... all features in one batch
]
```

### Things that go wrong

- **Team ID not cached.** Fetch once, reuse. Don't call `LINEAR_LIST_TEAMS` per issue create.
- **Workflow state IDs are project-specific.** "Done" in one team is not "Done" in another. Resolve state IDs once per session.

---

## Vercel

### Initial setup

1. `VERCEL_CREATE_PROJECT` — name = `<idea-slug>`, framework auto-detected from git import.
2. `VERCEL_LINK_PROJECT_TO_REPO` (if not done at create time).
3. Push to GitHub → Vercel auto-builds preview.

### Env vars

Always set vars in *both* `preview` and `production` environments unless the user specifies otherwise:

```json
COMPOSIO_MULTI_EXECUTE_TOOL [
  {"tool": "VERCEL_CREATE_ENV_VAR", "params": {"key": "SUPABASE_URL", "value": "...", "target": "preview"}},
  {"tool": "VERCEL_CREATE_ENV_VAR", "params": {"key": "SUPABASE_URL", "value": "...", "target": "production"}}
]
```

For secrets that differ between dev and prod (Stripe keys, etc.), set the dev value in preview and the prod value in production.

### Things that go wrong

- **Wrong framework detected.** If Vercel guesses wrong, set `framework` explicitly via `VERCEL_UPDATE_PROJECT`.
- **Build fails on Vercel but works locally.** Almost always a missing env var. Diff the local `.env.local` against `VERCEL_LIST_ENVIRONMENT_VARIABLES`.
- **Custom domain not propagating.** `VERCEL_LIST_DNS_RECORDS` to verify; can take 15–60 minutes.

### Verification

`VERCEL_LIST_DEPLOYMENTS` filtered to project_id, take the latest, confirm `state == "READY"` and `target == "preview"` (Phase 2) or `production` (Phase 5).

---

## Supabase

### Initial setup

1. `SUPABASE_CREATE_PROJECT` — name, region (us-east-1 default), plan (free).
2. Wait for `state == "ACTIVE"` (poll with backoff; takes 1–2 min).
3. Pull credentials: `SUPABASE_GET_PROJECT_URL`, `SUPABASE_GET_PUBLISHABLE_KEYS`.
4. Push these into Vercel env vars (`SUPABASE_URL`, `SUPABASE_ANON_KEY`).

### Migrations

DDL goes through `SUPABASE_APPLY_MIGRATION`, never `execute_sql` (which is read-only by design). This keeps schema changes in version control:

```
SUPABASE_APPLY_MIGRATION  name="0001_users_table"  query="CREATE TABLE ..."
```

The migration is recorded in the project's history and the agent can list past migrations with `SUPABASE_LIST_MIGRATIONS`.

### Branches

For risky migrations, create a Supabase branch (`SUPABASE_CREATE_BRANCH`), apply the migration there, exercise it, then `SUPABASE_MERGE_BRANCH` if green.

### RLS

Always enable RLS on user-data tables, even with permissive policies during dev. Easier to tighten later than to discover production is wide open.

### Verification

`SUPABASE_GET_ADVISORS` — runs Supabase's built-in advisor checks (security, performance). Run before every production deploy. Treat any P1 advisor as a Phase 4 blocker.

---

## Sentry

### Initial setup

1. `SENTRY_CREATE_PROJECT` (or via the integration's setup wizard if Composio + Sentry SDK auto-init is supported).
2. Add `@sentry/nextjs` (or framework equivalent) to the codebase.
3. Configure source map upload via the framework plugin (Webpack, Vite). Auth token goes in `GITHUB_ACTIONS_SECRET` or `VERCEL_ENV_VAR` — never in committed files.

### Verification (the test error pattern)

After setup, deliberately throw an error in a non-critical route:

```javascript
if (process.env.SENTRY_TEST === "1") {
  throw new Error("Sentry connectivity test — safe to ignore");
}
```

Hit the route on the deploy preview. Wait 30s. `SENTRY_SEARCH_ISSUE_EVENTS` filtered to that error message. If found and source maps are de-minified: green. If found but minified: source map upload is broken — fix before claiming Phase 4.

### Things that go wrong

- **Source maps minified.** Upload step is missing or wrong auth token. Most common Phase 4 blocker.
- **Replays not capturing.** Replay sample rate is 0 by default in some templates. Bump it for production after privacy review.

---

## PostHog

### Initial setup

1. `POSTHOG_CREATE_PROJECT` (or the user creates manually if their account is org-locked).
2. Install `posthog-js` (or server-side equivalent for SSR/API analytics).
3. Initialize in the app entry point with `posthog.init(key, {api_host})`.
4. **Identify the user** as soon as they log in, before any event fires:
   ```javascript
   posthog.identify(user.id, { email: user.email, plan: user.plan });
   ```

### Verification

After Phase 4 setup, sign up a test user on the deploy preview. Within 60s, check PostHog for the `$pageview` and `signed_up` events on that distinct_id. If under `anonymous_<...>` instead of the user.id, identify is firing too late.

### Feature flags

For dark-launching new features, create the flag in PostHog first, gate the code behind `posthog.isFeatureEnabled('flag_key')`, ship the code with flag off, flip the flag when ready.

---

## Stripe

### Initial setup (test mode only)

1. `STRIPE_CREATE_PRODUCT` for each pricing tier.
2. `STRIPE_CREATE_PRICE` linked to each product (recurring or one-time).
3. `STRIPE_CREATE_WEBHOOK_ENDPOINT` for the deploy preview URL — events `checkout.session.completed`, `customer.subscription.*`, `invoice.*`.
4. The webhook signing secret goes in Vercel env vars *per environment*. Test webhook secret in preview, separate webhook + secret for production.

### Pattern: a real test transaction

After setup:
1. Sign up a test user.
2. Click upgrade in the UI.
3. Stripe test card `4242 4242 4242 4242`.
4. Complete checkout.
5. Verify: webhook fires (`STRIPE_LIST_EVENTS` filtered to recent), DB updates the user's plan, UI reflects the new plan, PostHog event for `subscription_started` fires.

### Things that go wrong

- **Webhook signature mismatch.** Wrong secret in env (often production secret in preview env or vice versa). Stripe dashboard shows the mismatch in the webhook delivery logs.
- **Idempotency.** Re-delivered webhooks should not double-charge or double-update. Use `idempotency_key` on Stripe writes; in your DB, key off the Stripe event ID.

### Hard rule

**Never run live-mode Stripe operations from the agent unattended.** If the user wants to ship payments, that's a manual flip from test to live mode by the user, after which the agent can confirm via `STRIPE_LIST_EVENTS` that real events flow but should not initiate live writes.

---

## Figma

Read-only is the right default for an agentic build. The flow:

1. User shares a Figma URL.
2. Agent uses the relevant Figma MCP / Composio integration to fetch component metadata, variables, and screenshots.
3. Planner uses these as design context (Phase 1).
4. Generator references variable names from Figma when creating CSS variables in code, so a future "update Figma → re-sync" workflow is feasible.

Don't try to write back to Figma from the agent. The round-trip isn't worth it for an MVP.

---

## A note on rate limits

Most of these integrations have rate limits in the 50–500 req/min range. For a typical agentic build, you won't hit them. The exception is *bulk operations* (e.g., creating 50 Stripe products in a loop). Use Composio multi-execute (which respects per-integration concurrency) and add an explicit `await sleep(N)` if you're doing >100 calls in a tight loop.
