---
name: no-worktrees-routeready
description: RouteReady work happens directly on the branch — do not create git worktrees for phases
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bb317c1a-6ba6-4bc0-934a-12772ad1a537
  modified: 2026-08-28T23:07:42.201Z
---

Jeremy asked (2026-08-28) not to use git worktrees on RouteReady. Work directly on the feature
branch; do not create `.worktrees/<phase>` per phase even when a skill suggests it.

**Why:** worktrees isolate *files*, and RouteReady's work is almost entirely migrations applied
through the Supabase MCP to one shared live project (`omodvjvhsoqevhtsosqq`). File isolation buys
nothing when the thing being mutated is a single remote database — and it adds a real cost on
Windows, where removing a worktree hit `Permission denied` on both the directory and
`.git/worktrees/` metadata and needed a PowerShell force-remove to clean up.

**How to apply:** implement on the branch, commit per task, push to `origin`. The sequencing
discipline that mattered was never worktree-derived — it comes from migrations being strictly
ordered and applied to shared state, so implementation stays sequential regardless. See
[[routeready-sequential-migrations]].
