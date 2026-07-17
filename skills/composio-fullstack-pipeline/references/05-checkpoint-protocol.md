# Checkpoint protocol — `.agent/` artifacts

The harness lives or dies on its checkpoints. A clean handoff is the difference between "resume tomorrow" and "rebuild from memory."

## The four artifacts

```
.agent/
├── tasks.json       # Feature list — append-only descriptions, mutable status/passes
├── progress.md      # Append-only event log
├── state.json       # Snapshot of the current moment
└── handoff.md       # The cross-platform / cross-session note
```

Plus a `.gitkeep` so the directory survives a fresh clone.

## `tasks.json` — strict schema

```json
{
  "project": {
    "name": "<idea-slug>",
    "description": "<one-paragraph problem statement>",
    "stack": {
      "framework": "next.js@14",
      "database": "supabase",
      "deployment": "vercel",
      "auth": "supabase-auth",
      "payments": "stripe-test",
      "observability": ["sentry", "posthog"]
    },
    "created_at": "2026-04-29T14:00:00Z",
    "updated_at": "2026-04-29T18:30:00Z"
  },
  "features": [
    {
      "id": "F001",
      "category": "foundation",
      "description": "Initialize Next.js + GitHub repo + Vercel link",
      "steps": [
        "Create GitHub repo via Composio",
        "npx create-next-app@latest with TypeScript + Tailwind",
        "Initial commit and push",
        "Link Vercel project to GitHub repo",
        "Verify preview URL works"
      ],
      "status": "completed",
      "passes": true,
      "priority": "P0",
      "dependencies": [],
      "phase": 2,
      "difficulty": "S",
      "commit": "a3f4c12"
    }
  ]
}
```

### Rules (strict — these matter)

- **Descriptions and steps are immutable** once written. If scope changes, add a new feature; never edit an existing one. (Renaming a file is fine; rewriting a feature's description is not.)
- **Only `status` and `passes` may be updated** during a build by the generator.
- `passes: true` only after the verification gate (lint + typecheck + build + tests) is green. If a later feature regresses an earlier one, set `passes: false` and explain in `progress.md`.
- One feature `in_progress` at a time. The generator does not multi-task.
- `dependencies` blocks the generator: a feature cannot start until all its dependencies are `passes: true`.

## `progress.md` — append-only log

Plain markdown. One entry per meaningful event. Format:

```markdown
## 2026-04-29T14:00:00Z — Plan signed off
- 8 features queued
- Stack: Next.js + Supabase + Vercel + Stripe + Sentry + PostHog
- MVP scope: <one line>
- Top risk: <one line>

## 2026-04-29T14:42:00Z — F001 Initialize Next.js + GitHub + Vercel
- Generator (Sonnet)
- Commit: a3f4c12
- Tests: 0 (foundation feature)
- Build: pass
- Vercel preview: https://<idea-slug>-preview.vercel.app
- Notes: none

## 2026-04-29T15:10:00Z — Evaluator run after F001-F002
- All clean
- No P1s
```

Never edit a past entry. If you discover an entry was wrong, write a new entry that says so.

## `state.json` — current moment snapshot

Refreshed at every checkpoint. This is what a future Claude (you, tomorrow) reads first when resuming.

```json
{
  "session": {
    "started_at": "2026-04-29T14:00:00Z",
    "checkpointed_at": "2026-04-29T18:30:00Z",
    "model": "claude-sonnet-4-6",
    "subagent_model": "claude-haiku-4-5"
  },
  "auth": {
    "method": "subscription",
    "tier": "max",
    "verified_at": "2026-04-29T14:00:00Z"
  },
  "repo": {
    "path": "/Users/jswil/repos/<idea-slug>",
    "branch": "main",
    "head_sha": "a3f4c12",
    "uncommitted_changes": false
  },
  "build": {
    "status": "pass",
    "tests_passing": "12/12",
    "typecheck": "pass",
    "lint": "pass"
  },
  "deploy": {
    "preview_url": "https://<idea-slug>-preview.vercel.app",
    "production_url": null
  },
  "connections": {
    "github": "ok",
    "linear": "ok",
    "vercel": "ok",
    "supabase": "ok",
    "sentry": "not_connected",
    "posthog": "ok",
    "stripe": "ok"
  },
  "current_feature": {
    "id": "F003",
    "status": "in_progress",
    "started_at": "2026-04-29T18:25:00Z"
  },
  "next_action": "Generator implements F003 step 2 (database migration for users table)",
  "blockers": [],
  "handoff_notes": "F002 evaluator run flagged P3 about README — defer to F008 (docs sweep)."
}
```

Always overwrite `state.json` in full at each checkpoint. Don't try to do partial diffs.

## `handoff.md` — cross-platform note

Written for any future entity (the user, another agent, a different platform) that picks up the project. Updated at end of every session and at every major milestone.

```markdown
# Handoff — <idea-slug>

**Last updated:** 2026-04-29T18:30:00Z by Claude Sonnet 4.6 (Cowork session).

## What this project is
<one paragraph from the planner>

## What's deployed
- Production: <URL or "not yet">
- Preview: https://<idea-slug>-preview.vercel.app
- Repo: github.com/<user>/<idea-slug>

## What's next
<from state.json.next_action>

## Who pays for what
- Vercel: Hobby (free)
- Supabase: Free tier
- Stripe: test mode (no charges)
- Sentry: free dev plan
- PostHog: free tier (1M events/mo)

## Credential locations
- Vercel: connected via Composio (OAuth, no key on disk)
- Supabase: project keys in Vercel env vars
- Stripe: test keys in Vercel env vars; webhook secret per environment
- Sentry: DSN in Vercel env vars; auth token (for source maps) in GitHub Actions secrets
- PostHog: project key in Vercel env vars

## Known issues / backlog
- <P3 items not yet addressed>

## To resume
1. cd into the repo.
2. Verify auth: `echo $ANTHROPIC_API_KEY` should be empty; `/status` should show Subscription.
3. Read `.agent/state.json` for current moment.
4. Read `.agent/progress.md` tail for last 5 events.
5. Pick up at `state.json.next_action`.
```

## Checkpoint triggers

Checkpoint after:

- Feature complete (`passes: true`).
- 75% context fill.
- Tests pass (especially after a non-trivial test pass — that's a milestone).
- Before any risky refactor.
- When switching categories of work (e.g., from auth to payments).
- User request.
- End of session.
- Burn-rate projection shows depletion before next reset.

## Commit conventions

```
[CATEGORY] Brief description

Details (optional, multi-line ok).

Tests: <what was tested>
Feature: <id from tasks.json>
```

Categories: `[FEAT]`, `[FIX]`, `[REFACTOR]`, `[DOCS]`, `[TEST]`, `[CHORE]`, `[CHECKPOINT]`. Use `[CHECKPOINT]` for snapshots that aren't tied to a single feature.

Example:

```
[FEAT] Add Stripe checkout session endpoint

Creates POST /api/checkout that builds a Stripe checkout session
for the price IDs in the request body. Test-mode only.

Tests: integration test hits the endpoint and asserts a session URL is returned.
Feature: F006
```

## Resume protocol

When picking up an existing project (yours from yesterday, or an entirely new agent):

1. `cat .agent/state.json` — current moment.
2. `tail -50 .agent/progress.md` — recent events.
3. `cat .agent/tasks.json` — the feature list.
4. `git log --oneline | head -20` — actual commits to verify alignment.
5. Run `/status` to verify auth.
6. Run the connection catalog (`COMPOSIO_MANAGE_CONNECTIONS`).
7. If `state.json.build.status` was `pass`, re-run the verification gate (lint/typecheck/build/tests) to confirm it still is. Sometimes a dependency drift breaks things between sessions.
8. Pick up at `state.json.next_action`.
