# Failure modes — what breaks and how to recover

The recurring patterns that show up across real agentic full-stack builds. Each entry: the symptom, the root cause, the fix, and how to prevent it next time.

## Auth failures

### Silent pay-per-token billing

**Symptom:** the user gets a surprise Anthropic invoice; they thought they were on the Max subscription.
**Cause:** `ANTHROPIC_API_KEY` was set in the environment when Claude Code started. The API key takes precedence over the `/login` OAuth credential when both are present.
**Fix:** `unset ANTHROPIC_API_KEY` in their shell rc, restart Claude Code, run `/status` to confirm "Subscription."
**Prevention:** Phase 0 step 0.1 — never skip the env-var check.

### OAuth credential stops working mid-session

**Symptom:** Claude Code starts erroring out with auth-related messages partway through a long run.
**Cause:** Refresh token expired; OAuth session ended on Anthropic's side (rare but happens after very long idle gaps or after a password change).
**Fix:** Run `/login` again. The credential is re-issued; the agent picks up where it left off.
**Prevention:** for very long runs (>4h), checkpoint frequently so a re-login mid-build doesn't lose state.

### Headless run can't auth

**Symptom:** `claude -p "..."` in CI or a script fails authentication.
**Cause:** OAuth credentials require an interactive browser round-trip on first acquisition. If the credential file isn't already on disk, headless can't bootstrap it.
**Fix:** Run `/login` interactively once on the same machine; the credential persists. *Or*, for true CI use, switch to `ANTHROPIC_API_KEY` (the paid API surface) — Max-sub OAuth isn't licensed for CI per the April 2026 TOS.

## Connection failures

### Composio integration "connected" but calls fail

**Symptom:** The connection catalog says GitHub is connected, but every `GITHUB_*` call returns a 401 or 403.
**Cause:** OAuth token expired or revoked. Composio's catalog shows the *connection record* exists, not that the token is currently valid.
**Fix:** Run `COMPOSIO_MANAGE_CONNECTIONS` → reconnect for that app. Have the user re-do the OAuth round-trip.
**Prevention:** at session start, do a one-call health check against each integration the build will use, not just a catalog read.

### Native MCP and Composio both connected for the same app

**Symptom:** The agent oscillates between using GitHub MCP and Composio's GitHub actions; results come back in different shapes; nothing is consistent.
**Cause:** No clear preference rule.
**Fix:** Always prefer the native MCP for single-app actions when it's available. Composio for everything else and for multi-app workflows.
**Prevention:** in `state.json`, write down which integration provider you're using per app. The orchestrator reads this before any tool selection.

## Context failures

### Mid-feature context exhaustion

**Symptom:** The agent's responses get noticeably worse, hedge more, lose track of what it just wrote.
**Cause:** Context past 80% fill.
**Fix:** Stop. Checkpoint (`state.json` + `progress.md` + commit). `/clear`. Read `.agent/state.json` and the relevant feature from `tasks.json`. Resume.
**Prevention:** `/compact` at 50% fill. Don't start a complex feature past 70% fill.

### Stale context contaminating new feature

**Symptom:** While working on F005 (payments), the agent keeps re-reading F002 (auth) files unnecessarily, or worse, references behaviors that were since refactored away.
**Cause:** Context from earlier features wasn't cleared.
**Fix:** `/clear` between unrelated features. Reload only what F005 needs.
**Prevention:** Establish a habit of `/clear` at category transitions (auth → payments, frontend → backend, etc.).

### Subagent returns full transcript instead of summary

**Symptom:** A subagent that was supposed to research and return 500 tokens instead pastes back its 30,000-token exploration, blowing the orchestrator's context.
**Cause:** Vague subagent prompt — no explicit instruction to summarize or token cap.
**Fix:** Re-launch the subagent with a tighter prompt: "Return a 200-word summary; do not include search results verbatim."
**Prevention:** every subagent prompt ends with the expected output shape and word count.

## Build / deploy failures

### Local build green, Vercel build red

**Symptom:** `npm run build` works locally; Vercel deploy fails on the same commit.
**Cause:** Almost always a missing env var on Vercel that exists locally in `.env.local`.
**Fix:** Diff `.env.local` against `VERCEL_LIST_ENVIRONMENT_VARIABLES`. Add the missing ones to both `preview` and `production` environments.
**Prevention:** When adding any new env var, add it to all three places (`.env.local`, Vercel preview, Vercel production) in the same commit-and-push cycle.

### Migration runs locally, breaks production

**Symptom:** `SUPABASE_APPLY_MIGRATION` works on the project's main DB, then a column is "missing" in the deployed app.
**Cause:** The migration applied to the dev project but the app is talking to a different Supabase URL (e.g., env var still pointing to an old project).
**Fix:** Verify `SUPABASE_URL` in Vercel env vars matches the project that received the migration.
**Prevention:** before any migration, log the project URL the migration is targeting and compare to the deployed env var.

### Source maps minified in Sentry

**Symptom:** Sentry shows errors but the stack traces are minified (`a.b.c is undefined` style).
**Cause:** Source map upload step is missing from the build pipeline, or the auth token doesn't have the right scope.
**Fix:** Configure the framework's Sentry plugin (`@sentry/nextjs/webpack`) with `authToken` and `org`/`project` set. Add the auth token to GitHub Actions secrets and Vercel env vars.
**Prevention:** Phase 4 production gate item #1 includes "deliberate test error visible in Sentry **with un-minified stack**" — don't claim it green until that's true.

## Process failures

### Generator silently expands scope

**Symptom:** Reviewing the diff for F003 (search filtering), you find changes to F002 (auth) files that were not in F003's steps.
**Cause:** The generator decided "while I'm in there..." and made changes outside its assigned scope.
**Fix:** Revert the out-of-scope changes. Re-plan if those changes were actually needed (add as F009 to `tasks.json`).
**Prevention:** Generator prompt includes "Do not modify files outside the feature's stated steps. If you need to, return Blocked with a re-plan request."

### Evaluator rubber-stamps three runs in a row

**Symptom:** Three evaluator runs all return "all clear" — but visible bugs exist.
**Cause:** Evaluator prompt didn't actually require running the deploy preview or test suite. The evaluator is doing a static read.
**Fix:** Tighten the evaluator prompt: "Run the test suite. Hit the deploy preview URL. Report observed behavior."
**Prevention:** evaluator prompts always include explicit verification commands, not just "review the code."

### `passes: true` set without verification

**Symptom:** A feature is marked `passes: true` but tests don't actually exist for it, or the tests fail.
**Cause:** The generator (or worse, the orchestrator) skipped the verification gate.
**Fix:** Set `passes: false`. Run lint + typecheck + build + tests. Fix any failures. Set `passes: true` only when all green.
**Prevention:** the generator prompt has it as a hard rule. The evaluator double-checks it. The orchestrator should never override the rule.

## Stripe / payment failures

### Live-mode keys in dev

**Symptom:** A test transaction actually charges a real card.
**Cause:** Live-mode Stripe keys leaked into the dev/preview environment.
**Fix:** Refund immediately. Rotate the live keys (treat as compromised). Audit env vars across all environments.
**Prevention:** Hard rule — only test-mode keys go anywhere the agent can touch. Live keys are user-managed only.

### Webhook signature mismatch

**Symptom:** Stripe dashboard shows webhook delivery failures with "signature mismatch."
**Cause:** Webhook signing secret in the receiving env doesn't match the secret Stripe is using to sign.
**Fix:** Re-pull the webhook signing secret from `STRIPE_LIST_WEBHOOK_ENDPOINTS`. Update the receiving environment.
**Prevention:** webhook secrets are environment-specific; keep one per environment, never share.

## Database failures

### RLS off in production

**Symptom:** A user can read other users' data.
**Cause:** RLS was off during dev for convenience and never re-enabled.
**Fix:** Enable RLS immediately, write the right policies, test that cross-user access is blocked.
**Prevention:** Phase 4 production gate item #7. Run `SUPABASE_GET_ADVISORS` — it flags RLS-off tables.

### Backups never tested

**Symptom:** Disaster strikes; the user wants to restore from backup; the backup doesn't exist or doesn't restore cleanly.
**Cause:** Backups were "configured" but never actually exercised.
**Fix:** As part of Phase 4, do a drill: create a Supabase branch from a backup, verify it has the data you expect, delete the branch.
**Prevention:** backup-tested is part of the production gate — not "backups configured."

## When it's truly hosed

If the project is in a state you can't reason about:

1. `git stash` (or `git stash --include-untracked`) to preserve any in-flight work.
2. `git log --oneline | head -20` — find the last commit you trust.
3. `git checkout <SHA>` → look around → if it's clean: `git checkout main && git reset --hard <SHA>` *with user permission*.
4. Read `.agent/progress.md` to understand how you got into the bad state.
5. If `.agent/state.json` is also unreliable, regenerate it from current git state + a `pnpm test` (or equivalent) run.
6. Have a frank conversation with the user about what's salvageable.

Don't double down on a fix when the project is fundamentally confused. Stop, get oriented, and re-engage from a known-good state.
