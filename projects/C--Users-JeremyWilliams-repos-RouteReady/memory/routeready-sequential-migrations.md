---
name: routeready-sequential-migrations
description: "RouteReady migration work cannot be parallelized — one shared live Supabase project, ordered migrations"
metadata: 
  node_type: memory
  type: project
  originSessionId: bb317c1a-6ba6-4bc0-934a-12772ad1a537
  modified: 2026-08-28T23:07:53.991Z
---

RouteReady's Plan 1 applies every migration through the Supabase MCP to a single live project
(`omodvjvhsoqevhtsosqq`). Migration order is load-bearing and the repo file stem must equal the
`apply_migration` name, so repo history stays identical to applied history.

**Consequence:** implementation is inherently sequential. Two agents applying DDL concurrently would
race on schema state and break that parity. Fan out design, critique, review and verification —
never the migrations themselves. This holds no matter what an orchestration skill suggests.

**Fixing an already-applied migration:** never edit it in place. Add a letter-suffixed sibling
(`0006b`, `0007c`, `0008c`, `0009b`) — the convention established across Tasks 6-9.

Related: [[no-worktrees-routeready]].
