# Auth: Claude Code on the Max subscription

This is the first thing to verify and the most common silent failure. Get this wrong and the user pays per token instead of getting subscription-included usage. Worse, in some configurations the agent will *appear* to work and then the user gets a surprise bill at the end of the month.

## The rule

Use `/login` to authenticate Claude Code against the user's Max subscription via OAuth. Do **not** use `ANTHROPIC_API_KEY`. If both are present, the API key wins by default — silently.

## Pre-flight check

Before doing any real work, run these three checks in order.

### 1. Confirm `ANTHROPIC_API_KEY` is unset

```bash
echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:+SET}${ANTHROPIC_API_KEY:-UNSET}"
```

Expected: `ANTHROPIC_API_KEY=UNSET`.

If `SET`:
1. Identify where it's set: `~/.bashrc`, `~/.zshrc`, `~/.profile`, project `.env`, or shell-specific config.
2. Have the user remove or comment it out.
3. Either start a new shell session or `unset ANTHROPIC_API_KEY` in the current one.
4. Restart Claude Code.

### 2. Run `/login` if not already logged in

Inside Claude Code:

```
/login
```

This opens a browser tab to Anthropic's OAuth flow. The user signs in (or is already signed in to Claude.ai), approves the OAuth consent, and the credential is persisted on disk. The browser tab returns a "you can close this" page when done.

Credential file locations (as of 2026):
- macOS: `~/.config/claude/credentials.json` or the macOS Keychain.
- Linux: `~/.config/claude/credentials.json`.
- Windows: `%APPDATA%\Claude\credentials.json`.

These paths can change between Claude Code versions; if the user reports auth issues, have them run `claude --version` and check the docs at https://code.claude.com/docs/en/authentication for current locations.

### 3. Verify the active credential

Inside Claude Code:

```
/status
```

Expected output includes a line like `Authentication: Subscription (Max)` or similar.

If it says `API key`: go back to step 1 — the env var is still leaking in from somewhere.
If it says `Subscription (Pro)` and the user expected Max: they're logged into the wrong account. Have them log out and log back in to the Max-tier account.

## TOS scope (April 2026 policy — non-negotiable)

Anthropic's April 4, 2026 policy is unambiguous: OAuth credentials obtained via Claude Free / Pro / Max are licensed for use **only** in Claude Code and Claude.ai. Using these tokens in:

- The Claude Agent SDK (Python or TS) directly,
- Third-party harnesses that route requests via OAuth (OpenClaw, NanoClaw, etc.),
- Any wrapper that proxies the OAuth token to a non-Anthropic surface,

…constitutes a violation of the Consumer Terms of Service. This is enforced server-side.

**What this means for this skill:** drive everything through Claude Code. If the user asks for an Agent-SDK-based harness, that's fine — but it must use an actual `ANTHROPIC_API_KEY` for the API surface, separate from their Claude Code OAuth credential. Do not blur those two.

## Quotas and pacing on the Max subscription

Two-layer limits as of 2026:

- **Session window**: a 5-hour rolling window starts on first message. Resets 5 hours later.
- **Weekly cap**: total usage across all sessions, with separate buckets per model. Limits are shared across Claude.ai, Claude Desktop, and Claude Code on the same subscription.

Practical implications for an agentic full-stack build:

- Start a session 2–3 hours before intensive work begins (a lightweight prompt opens the window). The window resets mid-focus-block, giving access to two windows during peak hours.
- Default to Sonnet for most generation work. Reach for Opus only on architectural decisions or hard refactors.
- Route subagents to Haiku for research, summarization, and parallel reads. Set `CLAUDE_CODE_SUBAGENT_MODEL=haiku` to make this the default.
- `/compact` proactively at ~50% context fill (set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50`).
- If approaching weekly cap mid-build, downshift Sonnet→Haiku for routine work, or pause non-critical tasks until the next reset window.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Silent pay-per-token billing | `ANTHROPIC_API_KEY` set in env | `unset` it; verify with `/status` |
| `/login` redirects but never completes | Browser blocked the callback | Try a different browser; check firewall |
| Auth works, then expires mid-session | OAuth refresh token rejected | Re-run `/login` |
| `claude -p` headless run fails auth | Credential file not present in headless env | Run `/login` interactively first to seed the credential file, then run headless |
| Works on local, not in CI | OAuth not for CI use | CI must use `ANTHROPIC_API_KEY` (paid API surface), not Max-sub OAuth |

## Sources

- [Authentication — Claude Code Docs](https://code.claude.com/docs/en/authentication)
- [Managing API key environment variables in Claude Code](https://support.claude.com/en/articles/12304248-managing-api-key-environment-variables-in-claude-code)
- [Anthropic bans Claude subscription OAuth in third-party apps (Feb 2026)](https://winbuzzer.com/2026/02/19/anthropic-bans-claude-subscription-oauth-in-third-party-apps-xcxwbn/)
- [Claude API authentication in 2026: OAuth tokens vs API keys explained](https://lalatenduswain.medium.com/claude-api-authentication-in-2026-oauth-tokens-vs-api-keys-explained-12e8298bed3d)
