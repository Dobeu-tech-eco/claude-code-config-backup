# Pipeline phases — idea to production

The five phases are sequential. Phase 0 is mandatory. Phases 1–5 each have a clear exit gate; don't advance until the gate is green.

## Phase 0 — Pre-flight

Already covered in `SKILL.md`. Recap:
1. Verify `unset ANTHROPIC_API_KEY` and `/login` is active (`/status` shows Subscription).
2. Catalog Composio connections, surface gaps, walk user through `COMPOSIO_MANAGE_CONNECTIONS` for missing-but-needed apps.
3. Verify docs freshness for any framework the user names.
4. Scaffold `.agent/` from the templates in `assets/pipeline-template/`.

**Exit gate:** `state.json` exists with `auth: subscription`, connections cataloged, repo initialized.

## Phase 1 — Idea capture & scoping (planner)

**Goal:** turn the user's idea into a signed-off plan.

### Steps

1. **Listen.** Have the user describe the idea in their own words. Don't shape it yet. If they've shared a Figma file, attached docs, or referenced an existing app, fetch context for those *before* planning (parallel subagents on Haiku).

2. **Spawn the planner.** Subagent on Sonnet. Give it the prompt template from `references/03-three-agent-harness.md` § Planner. Inputs: the idea, the connection catalog, any constraints the user mentioned (budget, deadline, stack preference).

3. **Review the planner's output.** As the orchestrator, read it once with fresh eyes. Sanity-check:
   - Is the MVP genuinely minimal, or has the planner sneaked in a Phase 3 feature?
   - Are the integrations realistic given what's connected?
   - Are the risks meaningful and the mitigations actually mitigations?

4. **Present to the user.** Show the plan in chat. Highlight the three things you most want their input on (typically: stack choice, MVP scope cuts, top-1 risk).

5. **Iterate until sign-off.** Re-run the planner with their feedback as additional input. Do not start building until they explicitly say "go."

### Exit gate

- `.agent/tasks.json` is populated with ≤8 features, each with steps and a difficulty rating.
- User has signed off in chat.
- `progress.md` has its first entry: timestamp, "Plan signed off."

### Common traps

- **Skipping the user sign-off** because the plan "looks fine." Don't. The user's idea has constraints in their head you cannot see; surfacing them now is far cheaper than rebuilding later.
- **Letting the planner pick exotic infra.** Default to the boring stack: Next.js + Supabase + Vercel + Stripe + Sentry + PostHog. Deviate only with explicit user reason.
- **Treating the plan as immutable.** Re-plan when assumptions change. Just write the change to `tasks.json` and `progress.md` rather than letting the agent silently drift.

## Phase 2 — Foundation (generator)

**Goal:** get the boring-but-essential infrastructure in place and a deploy preview shipping.

### Foundation features (in order)

1. **Project init.** Create the GitHub repo, scaffold the framework (`npx create-next-app` or equivalent), commit the initial state. Composio multi-execute can do repo create + initial Vercel link in one batch.
2. **CI/CD basics.** GitHub Actions: lint, typecheck, test, build on every PR. Vercel auto-deploys preview on push.
3. **Auth.** Wire the auth provider (Clerk / Supabase Auth / NextAuth) with dev keys. Sign-up + sign-in + sign-out flows working locally.
4. **Database schema (v1).** Supabase migrations defining the core tables. RLS policies even if dummy. Seed script for local dev.
5. **Domain models.** TypeScript types and zod schemas for the core entities. One source of truth.
6. **One happy-path UI flow.** Logged-in user can do *one* thing the app is for. Doesn't need to be polished — needs to be end-to-end.
7. **One happy-path API flow.** Server-side equivalent of the same flow.
8. **Deploy preview.** A Vercel preview URL that shows the happy-path flow working with real (dev) data.

### Working pattern

For each feature, the generator runs solo per the prompt in `references/03-three-agent-harness.md`. After each feature: lint + typecheck + build + tests must all pass. Only then does `passes: true` go in `tasks.json`.

The orchestrator checkpoints after each feature: git commit + `progress.md` entry + `state.json` refresh.

### Exit gate

- All 8 foundation features are `passes: true`.
- The deploy preview URL is live and shows the happy-path flow working.
- An evaluator run on the foundation returns clean (no P1s).
- `state.json` is current.

## Phase 3 — Feature build-out (generator + evaluator)

**Goal:** ship the rest of the MVP scope.

### Working pattern

- Generator runs one feature at a time, same workflow as Phase 2.
- After every 2–3 features, run the evaluator subagent (`references/03-three-agent-harness.md` § Evaluator). When the evaluator flags P1s, generator fixes before advancing.
- Compact at 50% context. Reset (clear + read `.agent/` files) between unrelated features.
- Use git worktrees for *parallel* exploration of two competing approaches when scope is genuinely ambiguous. Discard the loser.

### Common Phase 3 features

- Real auth with production keys (vs the dev keys in Phase 2).
- Payment flow (Stripe in test mode).
- Search / filtering / sorting on the core list views.
- Email notifications (transactional only — Resend / Postmark / Sendgrid).
- File uploads (Supabase Storage / S3).
- Background jobs (Inngest / Trigger.dev / Supabase Edge Functions on a schedule).
- Multi-user / collaboration features.
- Admin dashboard (often last; defer to backlog if MVP doesn't need it).

### Exit gate

- All non-foundation features in `tasks.json` are `passes: true`.
- Evaluator's last report is clean.
- Deploy preview exercises every feature end-to-end without dev hacks.
- `state.json` is current.

## Phase 4 — Production hardening

Recapped from `SKILL.md`. The eight items in the production gate are non-negotiable for "production":

1. Observability (Sentry + source maps + a deliberate test error visible in Sentry; PostHog initialized + first event fires).
2. Real production auth keys.
3. Stripe configured in test mode with webhook signing secrets per environment.
4. No secrets in git history (`gitleaks`).
5. Lighthouse ≥90 on home page.
6. Keyboard navigation + AA contrast.
7. Database backups + RLS verified + a non-trivial migration tested on a Supabase branch.
8. Custom domain with SSL (if user has one).

Composio multi-execute handles most of the verification — query Sentry for events, query PostHog for the first event, query Vercel for env vars across both environments, query GitHub for branch protection. The agent confirms each box rather than reinventing the verification.

### Exit gate

All 8 boxes green. Not 7. Not "we'll come back to that one." Eight.

## Phase 5 — Launch and handoff

The launch is anticlimactic. By this point the production gate is green and the deploy preview is the production app.

1. Promote the latest preview to production (or push to `main` if Vercel is configured for auto-prod-on-main). One Composio call.
2. Verify the production URL.
3. Run one final user-facing smoke test together with the user (a real end-to-end transaction, sign-up, etc.).
4. Tag a release commit `v0.1.0`. Push the tag.
5. Open a "Post-launch backlog" issue (Linear or GitHub per user preference) seeded with everything the planner deferred.
6. Update `handoff.md` with: deployed URL, what's live, what's next, who pays for what (Vercel/Supabase/Stripe plans), credential locations, on-call expectations (typically: none, this is a side project — be honest if so).

### Exit gate

- Production URL responds 200 OK.
- Smoke test passed with the user.
- Release tagged and pushed.
- `handoff.md` is final.
- `progress.md` has a final entry: timestamp + "Shipped v0.1.0 to <URL>."

## When the user wants to keep going past v0.1.0

Loop back to Phase 1 with the same `.agent/` files. The planner reads existing `tasks.json` and the post-launch backlog as inputs and produces the v0.2.0 plan. The harness rinses and repeats.

There is no Phase 6. v0.1.0 → planning v0.2.0 is the same phase 1 you already ran, just with more context.
