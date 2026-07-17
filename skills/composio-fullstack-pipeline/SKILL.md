---
name: composio-fullstack-pipeline
description: Drives a long-horizon agentic full-stack build from raw idea to production deployment using Claude Code (Max-subscription auth via `/login`) and Composio for cross-system integration. Use this skill whenever the user wants to build, ship, or deploy a real software project end-to-end with an agent — landing pages, SaaS apps, internal tools, AI features, mobile/web full-stack, MVPs, side projects, or production systems. Trigger on phrases like "build me an app," "take this idea to production," "agentic coding," "code this for me," "ship a prototype," "scaffold a SaaS," "deploy to Vercel/Supabase/Netlify," "I have an idea for X," and any multi-day or multi-session coding workflow that needs checkpoints, GitHub/Linear/Vercel/Supabase/Sentry/PostHog/Stripe integration, or a planner→generator→evaluator harness. Use it even when the user hasn't explicitly named "Composio" or "Claude Code" — if the request is "build me a thing end-to-end," this skill applies.
---

# Composio full-stack pipeline

You are driving a long-horizon agentic build. The mission is simple to state and hard to execute: take the user's idea and ship it to production, surviving multi-hour or multi-day runs without burning the user's tokens, breaking their auth, or collapsing under context exhaustion.

This skill encodes the harness. It assumes Claude Code (the CLI/IDE coding agent) is the runtime and Composio is the universal tool layer for everything outside the local repo. It is opinionated about three things:

1. **Auth must use Claude Code's `/login` Max-subscription OAuth** — never the API key. See `references/01-auth-claude-code-max.md`. Per Anthropic's April 2026 policy, Max-sub OAuth is licensed for Claude Code and Claude.ai *only*; do not use it inside the Agent SDK or third-party harnesses.
2. **Use the planner → generator → evaluator three-agent harness** for anything past a single feature. Anthropic's published harness work (April 2026) is unambiguous: even Opus on the Agent SDK in a loop falls short on full-stack apps without this structure. See `references/03-three-agent-harness.md`.
3. **Composio is the integration spine.** Native MCP for single-app actions where it exists; Composio for cross-system workflows, bulk execution, and any app without a native MCP. See `references/02-composio-toolkit.md`.

## How to use this skill

Read this file fully on every invocation. Then follow the phase order below. Each phase has a one-line summary here and a deeper reference if the user is doing real production work. **Do not skip the pre-flight.** That's where most agentic full-stack builds silently fail.

---

## Phase 0 — Pre-flight (≤2 min, never skip)

Before discussing the idea, before writing a line of code, run the pre-flight. The pre-flight is short, cheap, and prevents the three highest-cost failures (wrong auth, missing connection, stale docs).

### Step 0.1 — Verify Claude Code auth is on the Max subscription

```bash
# In a terminal the agent controls:
echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:+SET}${ANTHROPIC_API_KEY:-UNSET}"
```

If `SET`, instruct the user to `unset ANTHROPIC_API_KEY` (or remove it from their shell rc) and restart the Claude Code session. The API key takes precedence over the OAuth credential when both are present, which silently drops them off the subscription and onto pay-per-token billing — the #1 reason agentic builds blow up a wallet.

Then have the user run `/status` inside Claude Code to confirm the active credential is "Subscription" (Max), not "API key."

If the user has not yet logged in, walk them through:

```
/login
```

This opens a browser tab to Anthropic's OAuth flow, completes the round-trip, and persists the credential on disk. Full detail in `references/01-auth-claude-code-max.md`.

### Step 0.2 — Catalog connections

Composio is the integration spine. Every full-stack build will touch at least three of: GitHub, Linear, Vercel, Supabase, Sentry, PostHog, Stripe, Figma, Slack, Gmail, Google Calendar, Notion. Confirm what's already connected before planning, because the plan branches on what's available.

Use Composio's connection-management tool to enumerate:

```
COMPOSIO_MANAGE_CONNECTIONS  → list_connections (or equivalent)
```

If a critical app for the user's idea is not connected, surface that *now* and offer to walk them through `COMPOSIO_MANAGE_CONNECTIONS` with the auth flow. Don't get five phases deep into a build and then discover Vercel isn't connected.

If a native MCP for a specific app is *also* connected (e.g., the GitHub MCP, Vercel MCP, Supabase MCP), prefer it over Composio for that one app — lower latency, richer schemas. Composio is for cross-app orchestration and the long tail. Decision tree in `references/02-composio-toolkit.md`.

### Step 0.3 — Verify docs freshness

For any framework / SDK / library the user names in their idea, do not trust your training data — fetch the current docs. Composio, Vercel, Supabase, Stripe, and Next.js all ship breaking changes regularly. Use WebSearch or the relevant native MCP to verify the canonical install/setup snippet before scaffolding.

### Step 0.4 — Scaffold the workspace

Create `.agent/` at the repo root with the four canonical artifacts:

```
.agent/
├── tasks.json       # The feature list (immutable descriptions + status/passes)
├── progress.md      # Append-only log: timestamp + what happened
├── state.json       # Snapshot: cwd, git SHA, build/test status, model, connections
└── handoff.md       # The cross-platform handoff note (kept current)
```

Templates in `assets/pipeline-template/`. Schemas and update rules in `references/05-checkpoint-protocol.md`.

---

## Phase 1 — Idea capture & scoping (planner)

The planner is the first of the three agents in the harness. Its job is *not* to write code. Its job is to turn the user's idea into:

1. A one-paragraph problem statement (what the user wants, who it's for).
2. A bounded MVP scope (the smallest thing that proves the idea works).
3. A tech-stack decision with rationale. Default to Next.js + Supabase + Vercel for web SaaS unless the user prefers otherwise — it's the highest-leverage stack for agentic builds in 2026, with the most battle-tested Composio integrations.
4. A feature list, broken into ≤8 features each with 3–6 implementation steps.
5. A risk register: what could go wrong, and the cheapest mitigation for each.

The planner runs as a subagent (Sonnet) so its exploration doesn't pollute the orchestrator's context. It returns a distilled plan — typically 600–1,200 tokens — that becomes `.agent/tasks.json` and the seed of `progress.md`.

**Ask the user to sign off on the plan before proceeding.** Re-planning is cheap; rebuilding a wrong feature is not.

Detailed planner prompt template and decision points in `references/04-pipeline-phases.md` (§ Phase 1).

---

## Phase 2 — Foundation (generator, one feature at a time)

Now we build. The generator is the second agent in the harness. It works *one feature at a time* from `tasks.json`, in dependency order. For each feature:

1. **Mark `status: in_progress`** in `tasks.json`. Never edit the description or steps.
2. **Write a failing test first** (TDD, where it makes sense — see `superpowers:test-driven-development` if installed).
3. **Implement the feature** in the smallest commit possible.
4. **Run the verification gate**: lint, typecheck, build, tests. All green or the feature does not advance.
5. **Commit**: `[CATEGORY] Brief description` per the convention in `references/05-checkpoint-protocol.md`.
6. **Mark `passes: true`** *only* after the verification gate is green. Never on assumption.
7. **Append to `progress.md`** with timestamp and what happened.

Foundation features come first, ordered roughly: project init → auth → database schema → core domain models → one happy-path UI flow → one happy-path API flow → deploy preview. The "deploy preview" milestone is critical; it forces the deployment integration (Vercel/Netlify/Railway/etc.) to be live by the end of Phase 2, not as a panicked Phase 5 surprise.

Use Composio's multi-execute for genuinely parallel actions (creating the GitHub repo + creating the Linear project + creating the Supabase project — all independent). Sequential for anything that depends on an earlier ID.

If the user is on a Max subscription with usage headroom, generation can run on Sonnet by default. Reach for Opus only for architectural decisions and complex refactors.

---

## Phase 3 — Feature build-out (generator + evaluator alternating)

Once the foundation exists and a deploy preview is green, alternate the generator and evaluator. The evaluator is the third agent in the harness. After every 2–3 generator features, run the evaluator as a subagent:

```
You are the evaluator. Read .agent/tasks.json and the recent commits (git log --since='2 hours ago').
Verify: (1) tests cover the new code, (2) types are sound, (3) no regression in foundation flows,
(4) integrations still work end-to-end (run a smoke test against the deploy preview).
Return a 200-word report flagging anything that needs to go back to the generator.
```

The evaluator's clean-context view catches drift the generator can't see from inside its own loop. When the evaluator flags issues, generator fixes before advancing.

**Context discipline** during this phase:
- `/compact` at 50% fill (set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` if in Claude Code).
- `/clear` between unrelated features.
- Never start a complex feature past 80% context — checkpoint and start fresh.
- Prefer subagents for any deep exploration ("which file does X?", "what does library Y do?"). They return 1–2k token summaries, the orchestrator stays clean.

Pattern catalog in `references/03-three-agent-harness.md` and `references/04-pipeline-phases.md` (§ Phase 3).

---

## Phase 4 — Production hardening

Before declaring done, run the production gate:

1. **Observability**: Sentry initialized, source maps uploaded, a deliberate error thrown end-to-end and confirmed visible in Sentry. PostHog initialized, one analytics event fires from the production build.
2. **Auth**: real auth provider (Clerk, Supabase Auth, NextAuth) configured with the *production* keys, not the dev keys. Sign-up, sign-in, sign-out paths exercised on the deploy preview.
3. **Payments** (if applicable): Stripe in *test mode* only — never live mode from an agent. Webhook signing secrets configured. Test a full purchase + refund cycle.
4. **Secrets**: env vars in Vercel/Netlify match `.env.example`; no secrets in git history (run `gitleaks` or equivalent).
5. **Performance**: Lighthouse / Core Web Vitals on the deploy preview. Target ≥90 on the home page.
6. **Accessibility**: keyboard navigation works on every primary path; color contrast ≥AA.
7. **Database**: backups configured, RLS policies on (Supabase), a non-trivial migration tested on a branch.
8. **Domain**: custom domain configured if the user has one; SSL active.

The production gate is a *checklist*, not creative work — most of it is best run via Composio's multi-execute against the relevant integrations, with the agent confirming each box rather than reinventing the verification.

Detailed production gate in `references/06-integration-cookbook.md`.

---

## Phase 5 — Launch and handoff

The build is "done" when:

- All `tasks.json` features are `passes: true`.
- The evaluator's last report is clean.
- The production gate is green.
- `progress.md` has a final entry with the deployed URL and a summary of what shipped.
- `handoff.md` is current and captures: what the project is, what's deployed, what's next, who pays for what (Vercel plan, Supabase plan, Stripe account), and the credential locations.

Tag a release commit `v0.1.0` and push. Open a Linear issue (or GitHub issue, per user preference) titled "Post-launch backlog" and seed it with anything the planner deferred from MVP scope. Walk the user through the deployed app for a smoke test.

---

## Cross-cutting protocols

These apply throughout, not just at one phase.

### Checkpoints

Trigger a checkpoint after: feature complete, at 75% context, after tests pass, before risky refactors, when switching categories of work, on user request, at end-of-session. A checkpoint is: git commit + `progress.md` entry + `state.json` refresh + (if needed) a `tasks.json` status update. Full schema in `references/05-checkpoint-protocol.md`.

### Cost-aware delegation

Orchestrator (Sonnet, occasionally Opus): planning, decisions, integration. Workers (Haiku): research, file reads, summarization, parallel exploration. Set `CLAUDE_CODE_SUBAGENT_MODEL=haiku` to route subagents to Haiku by default. Workers want sharp, well-defined tasks; orchestrators want judgment calls.

### Composio multi-execute

When you have N independent actions across Composio integrations (e.g., create-repo + create-linear-project + create-supabase-project + invite-collaborator), batch them into a single `COMPOSIO_MULTI_EXECUTE_TOOL` call. Sequential when later steps depend on earlier IDs. See `references/02-composio-toolkit.md`.

### Failure recovery

When something breaks: stop, don't double down. Read the error, check the last green commit (`git log --oneline | head -10`), decide whether to (a) fix forward, (b) revert and retry, or (c) escalate to the user. Never silently `git reset --hard` without confirmation. Recovery patterns in `references/07-failure-modes.md`.

### Blast-radius approval gates

Before any of the following, pause and ask the user explicitly:

- Pushing to a `main` branch the user owns.
- Spending real money (live-mode Stripe, paid plan upgrade, paid domain purchase).
- Deleting any resource (repo, branch, database, deployment, table, customer record).
- Sending email or messages to people other than the user.
- Touching production data of any kind.

For low-risk reads, scaffolding, and explicitly requested actions, proceed without friction.

---

## When *not* to use this skill

- The user wants a one-line code answer or a quick refactor — that's a single tool call, not a pipeline.
- The user wants a static document/report (use the docx, pptx, or canvas-design skills).
- The user is debugging a single failing test (use `superpowers:systematic-debugging`).
- The user wants to design without building (use `design:critique` or `design:design-system`).

If the request is "make a thing exist that didn't exist," this skill applies. If it's "explain / fix / refactor an existing thing," it doesn't.

---

## Reference files

- `references/01-auth-claude-code-max.md` — `/login` flow, API-key conflict resolution, TOS scope.
- `references/02-composio-toolkit.md` — Composio essentials, multi-execute, MCP vs SDK decision tree, top integrations.
- `references/03-three-agent-harness.md` — Planner / generator / evaluator pattern, prompt templates, when to compact vs reset.
- `references/04-pipeline-phases.md` — The five phases in detail, with prompts for each.
- `references/05-checkpoint-protocol.md` — `.agent/` artifacts, schemas, commit conventions, handoff format.
- `references/06-integration-cookbook.md` — Concrete recipes for GitHub/Linear/Vercel/Supabase/Sentry/PostHog/Stripe/Figma.
- `references/07-failure-modes.md` — The recurring failure patterns and how to recover.

## Scripts

- `scripts/verify_auth.sh` — One-shot pre-flight check (API-key absent + `/login` active).
- `scripts/bootstrap_session.sh` — Catalog connections, scaffold `.agent/`, seed checkpoints.
- `scripts/checkpoint.sh` — Write `.agent/state.json` from current git+test+build status.

---

A note on philosophy: this is not a magic incantation. Agentic full-stack builds work because of *discipline* — pre-flight, three-agent harness, checkpoints, verification gates, blast-radius approval — not because of cleverness. Stay on the rails. The rails work.
