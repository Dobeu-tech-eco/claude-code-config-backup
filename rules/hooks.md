# Hooks System

<!-- review: 2026-09-09 — reconciled against actual settings.json; prior "Current Hooks" list was fiction -->

## Hook Types

- **PreToolUse**: Before tool execution (validation, blocking)
- **PostToolUse**: After tool execution (auto-format, checks)
- **UserPromptSubmit / SessionStart / Stop / SessionEnd / PreCompact**: lifecycle points

## Two things that are easy to get wrong

- **`timeout` is in SECONDS, not milliseconds.** `"timeout": 15000` means 4h10m, not 15s.
- **PreToolUse blocks on exit 2 and ONLY exit 2.** Exit 1 is a *non-blocking* error: Claude Code
  prints stderr and runs the command anyway. A blocking hook that exits 1 is silently a no-op.
  A PreToolUse hook that *times out* also does not block — so don't set a security gate's timeout
  too tight.

## Current hooks in `C:\Users\JeremyWilliams\.claude\settings.json`

One, deliberately:

| Event | Matcher | Hook | Timeout |
|-------|---------|------|---------|
| PreToolUse | `Bash` | `hooks/pre-commit-secret-scan.ps1` — scans staged files on `git commit`, exit 2 blocks | 20s |

It has a zero-subprocess fast path (a raw substring check for "commit" before JSON parsing, then a
`git...commit` regex check before touching the filesystem), so non-commit Bash calls are cheap. It
fails open on any unexpected condition (no git, no repo, malformed payload).

**Everything else comes from plugins, not from settings.json.** OMC registers ~19 hook entries
(UserPromptSubmit keyword-detection + skill injection, SessionStart, PreToolUse enforcement,
PostToolUse verification, Stop, PreCompact, SessionEnd); ECC registers ~23 more. That is ~42
registrations before this file adds anything, so a hook added here is purely additive on a hot path
— add one only when no plugin already covers it.

## Capabilities provided by plugins (do not re-add here)

- **Format + typecheck** — ECC batches these once per turn at Stop (`stop:format-typecheck`),
  rather than running a whole-project `tsc --noEmit` after every edit. For per-edit type feedback
  use OMC's `lsp_diagnostics` MCP tool instead; it is far cheaper.
- **console.log audit** — ECC `stop:check-console-log`, once per turn, with test/config/script
  exclusions.
- **Skill routing** — OMC's `keyword-detector` + `skill-injector` on UserPromptSubmit.

## ECC hook profiles

`ECC_HOOK_PROFILE` is unset, so it defaults to `standard`. ECC's own commit-quality secret scan,
tmux reminder, and git-push reminder are `strict`-profile only and are therefore **off**. Setting
`strict` turns on all of them together — a deliberate choice, not a like-for-like swap for the
secret scanner above.

`ECC_DISABLED_HOOKS` in settings.json disables three ECC hooks by id, including
`pre:config-protection` (which would otherwise guard `settings.json` against edits).

## Debugging

- `/hooks` lists every hook registered for the session, grouped by event. If a hook you defined is
  missing, it isn't being read — hooks belong under the `"hooks"` key of a settings file.
- A matcher is a single string; use `|` to match multiple tools (`"Edit|Write"`). An array value is
  a schema error and invalidates the whole settings file.
- `claude --debug` logs each event, the matchers checked, and each hook's exit code.

## Auto-Accept Permissions

Use with caution:
- Enable for trusted, well-defined plans
- Disable for exploratory work
- Never use the dangerously-skip-permissions flag
- Configure permissions in `settings.json` / `settings.local.json` instead

## TodoWrite Best Practices

Use TodoWrite tool to:
- Track progress on multi-step tasks
- Verify understanding of instructions
- Enable real-time steering
- Show granular implementation steps

Todo list reveals:
- Out of order steps
- Missing items
- Extra unnecessary items
- Wrong granularity
- Misinterpreted requirements
