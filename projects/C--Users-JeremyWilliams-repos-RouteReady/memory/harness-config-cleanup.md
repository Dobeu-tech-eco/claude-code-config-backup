---
name: harness-config-cleanup
description: Gemini stop-gate noise (RESOLVED 2026-09-10) plus still-open shadowed skills and MCP issues
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 55ade103-f0f4-40c5-b264-3ed9dbef7ad8
  modified: 2026-09-10T11:30:49.945Z
---

## 1. Gemini stop-review gate — RESOLVED 2026-09-10

The Gemini Code Assist individual free tier is no longer supported for the
`@google/gemini-cli` client, so every Stop hook fired a review that died with
`IneligibleTierError`. Failed 11+ times across two sessions.

**The off switch is `config.stopReviewGate` in the plugin's PER-WORKSPACE state
file — nothing else.** `gemini-abiswas97-gemini/state/<slug>-<hash>/state.json`
under `~/.claude/plugins/data/`. `stop-review-gate-hook.mjs` does
`if (!config.stopReviewGate) return;` and there is **no env kill switch and no
CLI flag** (`gemini-companion.mjs` exposes setup/review/task/status/... only).

Set to `false` in all three workspace states on 2026-09-10; verified via
`gemini-companion.mjs setup --json` → `reviewGateEnabled: false`.

**Two traps if this recurs:**
- `setup --json` reporting `ready:true, auth.loggedIn:true` is a **false
  positive** — it only assumes auth from `GOOGLE_API_KEY`/ADC presence and never
  makes a live call. Trust the runtime error, not the probe.
- A write to state.json is **clobbered by an in-flight review job** (900s hook
  timeout) that rewrites the whole object from its in-memory copy. Confirm no
  job is running, then write and re-read to verify it stuck.

**Superseded guidance:** the earlier note here said to disable it via
`~/.claude/settings.json` or `ECC_DISABLED_HOOKS`. Both are wrong — this hook is
registered by the gemini plugin's own `hooks/hooks.json` and is not an ECC hook.

## 2. Skill conflicts (23 shadowed) — still open

Identical skills in both `~/.agents/skills/` and `~/.gemini/skills/`, with
`.agents/` winning: `adaptive`, `android-cli`, `appfunctions`, `camerax`,
`android-profiler`, `android-intent-security`, `agp-9-upgrade`,
`display-glasses-with-jetpack-compose-glimmer`, `edge-to-edge`,
`engage-sdk-integration`, `leanback-to-compose-tv-migration`,
`media3-cast-integration`, `migrate-xml-views-to-jetpack-compose`,
`navigation-3`, `play-policy-insights`,
`play-billing-library-version-upgrade`, `r8-analyzer`, `styles`,
`testing-setup`, `verified-email`, `wear-compose-m3`. Plus `skill-creator`
overrides the built-in. Harmless (`.agents/` wins) but stale `.gemini/` cruft.
Fix: delete the `.gemini/skills/` duplicates.

## 3. MCP issues — still open

Run `/mcp list` and fix connectivity.

**Why:** the stop-gate failures blocked clean session ends and buried real output
in stderr noise. Items 2 and 3 are cosmetic/diagnostic, not blocking.

**How to apply:** item 1 needs no action unless the gate is re-enabled. Do 2 and 3
as one-time harness maintenance, not before RouteReady work. All of this is
machine-level config, unrelated to the RouteReady codebase. See
[[no-worktrees-routeready]].
