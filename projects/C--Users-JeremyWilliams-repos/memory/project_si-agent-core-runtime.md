---
name: si-agent-core-runtime
description: How to actually get the si-agent tuner loop running on this Windows machine — the WSL venv symlink trap and what makes the claude-code backend ready
metadata: 
  node_type: memory
  type: project
  originSessionId: c8c98d02-007d-48a0-8971-e28c90c20b63
  modified: 2026-09-23T02:57:14.424Z
---

Running the `si` CLI in `repos\si-agent-core` on this Windows box has two recurring
environment traps:

1. **`.venv\lib64` is a WSL-created symlink Windows cannot delete.** Any bare `uv run si ...`
   dies with `failed to remove file ...\.venv\lib64: Access is denied. (os error 5)` because uv
   tries to recreate the venv. Fix: point uv at an off-repo Windows-native environment,
   `UV_PROJECT_ENVIRONMENT=<some path outside the repo>`, rather than deleting `.venv` —
   that venv belongs to the user's WSL side.

2. **The `claude-code` backend is ready only when Claude Code is logged in *in that shell*.**
   Verified: after `/login`, `si doctor` reports `auth_source: host-login`,
   `billing_surface: host-plan`, `ready: true`, and a dev-split eval completes real model calls.
   Per a prior cloud session's report (not observed directly here), a sandbox bridge exposes a
   `claude` binary locked to bare `claude -p "<prompt>"` that rejects the flags the tuner needs,
   giving an instant `provider_failure` with zero model calls spent. Either way: run the loop
   where a real login lives.

`.si-agent/` (including `store.db`) is gitignored, so runs never dirty the tree.

**Why:** A prior session burned three attempts on these two things before concluding the cycle
could not run at all.

**How to apply:** Before running any `si eval`/`optimize`/`promote`, run
`uv run si doctor --format json` and confirm `ready: true`. See
[[si-agent-promotion-boundary]] for the approval rule on promote/rollback.
