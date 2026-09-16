---
name: dobeu-eco-connector-audit
description: >
  Runs Jeremy Williams' weekly READ-ONLY connector & instrumentation audit
  for the Dobeu-tech-eco GitHub org — smoke-tests Amplitude, Mixpanel,
  Datadog, PostHog, Google Analytics, Intercom, and GitHub via Composio,
  rebuilds the repo x analytics-platform instrumentation matrix across the
  14 active app repos, checks whether already-rolled-out apps are actually
  emitting events, appends a dated section to the analytics-observability
  goal-plan doc in the "Ruflo my GitHub" claude.ai Project, and pushes a
  notification only when something regressed. Use this skill whenever
  Jeremy asks to "run the connector audit", "check the Dobeu instrumentation
  matrix", "audit analytics/observability across my repos", "see if PostHog
  is still broken", or similar — even if he doesn't name every platform, and
  even outside the Monday schedule (e.g. "run this now", "did anything
  change since last week"). Never use this to install, merge, push, or
  delete anything — it is strictly a read-and-report skill.
---

# Dobeu-tech-eco weekly connector & instrumentation audit

This captures a recurring, previously ad-hoc audit as a repeatable procedure so it produces the same shape of result whether it fires from the Monday scheduled task or gets run on demand mid-week. The audit answers three questions every time: are the connectors we depend on still working, has any repo's instrumentation drifted since last week, and are the apps that claim to be instrumented actually sending events. It is read-only by design — the value here is visibility, not remediation, so never install, merge, push to, or delete anything in scope while running it.

## Before you start

Read the context doc first — it is the source of truth, not this file:

**Project:** claude.ai Project "Ruflo my GitHub"
**Doc:** `claude/dobeu-eco-analytics-observability-goal-plan.md`

That doc holds the target-state definition, last week's connector-health table, the last repo x platform matrix, and the currently-known blockers (as of the last run: PostHog auth broken, GA4 auth-ok-but-zero-properties). Read it with `project_read` before doing anything else — you're diffing against it, and you append to it at the end rather than replacing it.

If the doc's repo list, connector accounts, or target platforms have changed since this skill was written, trust the doc over the hardcoded values below and update this file's "Current configuration" section to match — it's meant to track reality, not the other way around.

## Current configuration

- **GitHub org:** Dobeu-tech-eco, via Composio account `github_big-lain`
- **Active app repos (14):** accident-dobeu, DOT-Copilot, statminer, dev_usp-com, ecc, restaurant-managemen, lastplateprod, dts-contract-engine, dobeu-design-system, dobeutech-sales-funnel-itconsult, ikram-meme-and-co, ai-tutor, ripple-positive-impa, new-dobeu-net
- **Reference implementation:** new-dobeu-net — should show all six platforms; use it to sanity-check the detection logic if a scan comes back suspiciously empty
- **Connectors (Composio account, unless noted):**
  - Amplitude — `amplitude_arided-fagger` (or native Amplitude MCP `get_amplitude_context`)
  - Mixpanel — `mixpanel_tedder` (or native Mixpanel MCP `Get-Projects`)
  - Datadog — `datadog_ego-cash`, proxy `GET https://api.datadoghq.com/api/v1/validate`
  - PostHog — `posthog_pepper`, proxy `GET https://us.posthog.com/api/organizations/@current/` (composio-only, no native MCP)
  - Google Analytics — `google_analytics_moschi-vizard`, proxy `GET https://analyticsadmin.googleapis.com/v1beta/accountSummaries`
  - Intercom — native MCP only (`list_companies`), workspace `xu0gfiqb` — Composio never completed auth for this one, don't retry it there
- Prefer Composio for GitHub and any account explicitly listed above; prefer native MCP tools when both exist and the doc doesn't say otherwise (Amplitude, Mixpanel) — it's lower-latency and has richer schemas.

## The five steps

Run these in order. Steps 1 and 2 are independent of each other and can run in parallel (e.g. via `COMPOSIO_REMOTE_WORKBENCH` fan-out or a couple of subagents) if you have that available; step 3 depends on step 2's results; steps 4 and 5 depend on everything before them.

### 1. Connector health

One cheap read call per connector, recorded as ACTIVE or BROKEN with the evidence (status code, error body, or the actual data returned):

- GitHub: `GITHUB_SEARCH_REPOSITORIES q="org:Dobeu-tech-eco"`
- Amplitude: `get_amplitude_context` (no projectId) or Composio equivalent
- Mixpanel: `Get-Projects` or Composio equivalent
- Datadog: the `/api/v1/validate` proxy call
- PostHog: the `/api/organizations/@current/` proxy call — this one was BROKEN (401) as of the last known-good run; check whether it's still broken and flag either way, don't assume it's fixed just because it was flagged before
- Google Analytics: the `accountSummaries` proxy call — known issue was zero GA4 properties returned even though auth succeeds; note whether that's still the case
- Intercom: `list_companies` on workspace `xu0gfiqb`

A connector is BROKEN if the call errors, times out, or returns something that doesn't look like real data (e.g. GA4 returning zero properties counts as a distinct flagged condition, not a hard BROKEN, since auth itself works).

### 2. Instrumentation audit

For each of the 14 repos, fetch the root `package.json` via `GITHUB_GET_REPOSITORY_CONTENT` (the file content is base64 under `data.content.content` — decode it before parsing). Look at `dependencies` and `devDependencies` for matches to each platform:

| Platform | Look for |
| --- | --- |
| Amplitude | `amplitude` (e.g. `@amplitude/unified`) |
| PostHog | `posthog-js` |
| Mixpanel | `mixpanel-browser` |
| Datadog | `datadog`, `dd-trace` |
| Google Analytics | `react-ga`, `@next/third-parties`, `google-analytics` |
| Intercom | `intercom` (e.g. `messenger-js-sdk` variants) |
| Sentry / Vercel Analytics | `@sentry`, `@vercel/analytics` — track these too even though they're outside the six-platform goal; they're useful context for the matrix |

Build a repo x platform matrix from this. Root `package.json` only catches top-level deps — if a repo has sub-apps (e.g. a nested app directory), note that the scan is root-only rather than silently treating a miss as "not instrumented." Also note that GA is often a raw `<script>`/gtag snippet with no npm dependency, so a dependency-only scan will under-report GA — flag repos where GA might be present via script tag but wasn't caught, rather than asserting confidently that GA is absent.

Diff this matrix against the one in the context doc from last time. Call out, explicitly:
- any repo that **lost** a platform it had before (this is the main regression signal — flag it prominently)
- any repo that **gained** a platform since last time (progress, worth noting even though it's good news)
- repos unchanged (fine to summarize as a single line, no need to enumerate)

### 3. Functioning check

For repos the context doc's status section marks as already rolled out, verify events are actually arriving — don't just trust that the dependency is installed. Query each relevant platform for recent `telemetry_selftest` events or any traffic from that app in the last several days (Amplitude chart/dataset query, Mixpanel `Run-Query`, PostHog events API, Datadog logs/RUM, as applicable to what that repo claims to have). Skip apps the doc says aren't rolled out yet — querying for events that were never supposed to exist just produces noise.

If a previously-verified app has gone silent (dependency present, but no recent events), that's a regression worth flagging even though the matrix cell itself didn't change — the instrumentation exists but stopped working.

### 4. Update the memory doc

Read the context doc again if meaningful time has passed since step 0 (someone else may have touched it), then append — never overwrite — a new dated section (`## <date> audit`) containing:
- the connector health table from step 1
- the current repo x platform matrix from step 2
- an explicit week-over-week diff: what changed, what stayed the same, what's still a known blocker
- the functioning-check results from step 3, especially any newly-silent apps

Write it back with `project_write` to the same path (`claude/dobeu-eco-analytics-observability-goal-plan.md`). This doc *is* the audit's memory — future runs (including future invocations of this skill) diff against whatever you just wrote, so be precise rather than terse; a vague "looks fine" entry breaks next week's diff.

### 5. Decide whether to notify

This is the step people actually feel, so get the bar right: silence is the correct outcome most weeks. Send a push notification only when at least one of these is true:

- a connector that was ACTIVE last time is now BROKEN
- PostHog or GA4 are *still* broken (the known blockers persisting isn't news, but if you're running unattended — e.g. from the scheduled Monday firing — a periodic reminder that a blocker is still live is more useful than the same silent nothing every week; use judgment about cadence if you're not sure whether one already went out recently)
- a repo lost instrumentation it had last week
- a previously-verified app stopped emitting events

If everything matches last week and the known blockers are unchanged, don't notify — send the update to the doc and stop there. When you do notify, lead with the single most actionable fact (what broke, when, which repo/connector) so the phone-banner sentence alone tells Jeremy what he needs to know.

## Notes on failure modes

- If a Composio account listed above returns an auth/connection error, don't spend time debugging or reconnecting it mid-audit — record it as BROKEN with the error and move on; reconnection is Jeremy's call, not something to fix inline.
- If GitHub content fetch fails for a specific repo (renamed, deleted, access revoked), don't fail the whole audit — mark that repo's row as "unreadable" in the matrix with the reason, and keep going with the rest.
- Never take any write action against GitHub, Vercel, or any connected platform beyond the read/proxy-GET calls listed above. If something in the audit looks like it needs a fix (e.g. PostHog needs reconnecting, GA needs a property created), that's a finding to report, not something to do.
