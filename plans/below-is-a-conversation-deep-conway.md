# Fix: Codex Stop-Review-Gate blocking every session Stop

## Context

The `openai-codex` plugin's Stop hook runs a "stop-gate review" via a spawned
`codex app-server` process on every turn end, and blocks the session from
stopping if that review doesn't return a clean `ALLOW:`. Starting today
(2026-08-14, ~09:20) this has failed on **every** attempt — 6 consecutive
failed jobs, each erroring with `codex app-server connection closed.` after a
Node `DEP0190` deprecation warning. This is a real regression, not a
long-standing config issue: the same gate completed successfully with
`ALLOW:` on 2026-07-16. The result is a hard loop — every Stop event
re-fires the same failing review and re-blocks, which is why the identical
hook-feedback message kept repeating verbatim across multiple turns.

State evidence (read-only inspection, all under
`C:\Users\JeremyWilliams\.claude\plugins\data\codex-openai-codex\state\JeremyWilliams-691eb02bda33a3a7\`):
- `state.json` → `"config": { "stopReviewGate": true }`, with 6 failed jobs
  today, all `errorMessage: "codex app-server connection closed."`
- `jobs\task-mssqvahw-9p3rya.log` → only contains a start line, no useful
  stderr (the hook's own stderr capture is what's shown to the user).

Root cause in plugin code
(`C:\Users\JeremyWilliams\.claude\plugins\cache\openai-codex\codex\1.0.6\scripts\lib\app-server.mjs:190-196`):

```js
this.proc = spawn("codex", ["app-server"], {
  ...
  shell: process.platform === "win32" ? (process.env.SHELL || true) : false,
  ...
});
```

On Windows, `SHELL` is a POSIX env var that's normally unset, so this spawns
`codex app-server` with `shell: true` — triggering the `DEP0190` warning —
and the child process appears to exit/error before the JSON-RPC `initialize`
handshake completes, which the client reports as `connection closed`.

The Stop hook itself
(`...\codex\1.0.6\scripts\stop-review-gate-hook.mjs:166-173`) treats any
non-`ok` review result as `{ decision: "block", reason: ... }`, which is
what's forcing the repeated blocking.

## Plan

1. **Stop the loop immediately** — set `stopReviewGate: false` in
   `C:\Users\JeremyWilliams\.claude\plugins\data\codex-openai-codex\state\JeremyWilliams-691eb02bda33a3a7\state.json`.
   This is the plugin's own supported config (defaults to `false` in
   `lib/state.mjs`), not a hack — it just turns the optional gate back off
   until the underlying spawn issue is fixed.
2. **Diagnose the CLI itself** (read/investigate, not required to unblock,
   but explains *why* it broke today after working 2026-07-16):
   - `where codex` / `codex --version` to confirm the CLI is still on PATH
     and functioning standalone.
   - `codex app-server` run manually to see the real stderr the hook's
     capture is missing.
   - Check for a recent `codex` CLI auto-update or `openai-codex` plugin
     version bump around 2026-08-14 that could have changed the app-server
     handshake or Windows spawn behavior.
3. **Re-enable once fixed** (optional, later) — after confirming
   `codex app-server` initializes cleanly standalone, flip
   `stopReviewGate` back to `true` if the review gate is still wanted, or
   leave it off if it's not valuable enough to maintain.
4. **Record the finding** — save a short project/feedback memory noting
   this is a known Windows-only regression in `openai-codex@1.0.6`'s
   `shell: true` fallback, so a future session doesn't re-diagnose it from
   scratch.

## Verification

- After flipping `stopReviewGate` to `false`, confirm the next session Stop
  completes without hook feedback/blocking.
- If diagnosing further, confirm `codex app-server` (run directly, outside
  the hook) either initializes successfully or produces a clear error that
  explains the regression.
