# Hooks

- Composio plugin provides SessionStart + UserPromptSubmit hooks (enabled via composio@composio).
- Historical guide lives on Google Drive as a .gdoc (cannot copy as binary): 
  G:\My Drive\ai-content\Claude-code\Claude hooks\Claude Code hooks- comprehensive technical guide.gdoc
- Add custom Claude Code hooks to this directory or via settings.json "hooks" when ready.

## Active hooks (Windows / PowerShell)

Registered in `~/.claude/settings.json`. Each reads the hook payload JSON from stdin.

| Script | Event | Matcher | Behavior |
| --- | --- | --- | --- |
| `pre-commit-secret-scan.ps1` | PreToolUse | `Bash` | Exits 0 silently unless the command is a `git commit`. On a commit, scans staged files for secret patterns and high-entropy key prefixes (`ghp_`, `sk-proj-`, `sk-ant-`, `ntn_`, `tvly-`). **Blocking** (`exit 1`) on a hit. |
| `post-edit-format.ps1` | PostToolUse | `Edit\|Write` | For `.ts/.tsx/.js/.jsx` only: runs `prettier --write`, then `npx tsc --noEmit` if a `tsconfig.json` is found at the nearest package root. **Never blocks** (always `exit 0`). |
| `post-edit-console-log.ps1` | PostToolUse | `Edit\|Write` | For `.ts/.tsx/.js/.jsx` only: warns on stderr with line numbers of any `console.log`. **Never blocks** (always `exit 0`). |

Matchers are a plain regex matched against the **tool name**. Filtering on command
content or file path happens inside the script, by parsing the stdin JSON payload
(`.tool_name`, `.tool_input.command`, `.tool_input.file_path`).

## legacy-linux-hooks.json.reference

`legacy-linux-hooks.json.reference` is a verbatim copy of an older Linux hooks
bundle, kept **for reference/provenance only**. It is **NON-FUNCTIONAL** and is
deliberately not wired into `settings.json`. Do not copy it back in. It is broken
two independent ways:

1. **Invalid matcher syntax.** Every entry uses an expression-language matcher such as
   `"matcher": "tool == \"Bash\" && tool_input.command matches \"git commit\""`.
   Claude Code matchers are a plain **regex against the tool name** (`"Bash"`,
   `"Edit|Write"`). As written, none of these hooks fire on any OS.
2. **Linux-only and hostile.** Every hook body is `#!/bin/bash` + `jq`, neither of which
   is on this machine's default path. Beyond portability, three of them are actively
   destructive and were **deliberately dropped**, not ported:
   - *tmux dev-server blocker* — unconditionally `exit 1`s on `npm/pnpm/yarn/bun run dev`
     demanding the command be relaunched under tmux. tmux does not exist on Windows, so this
     would brick every dev server with no escape hatch.
   - *git push pause* — calls a blocking `read -r` to wait for an interactive Enter keypress.
     Hangs any non-interactive/agent session indefinitely.
   - *block-all-.md/.txt writes* — blocks `Write` to any `.md`/`.txt` file not named
     README/CLAUDE/AGENTS/CONTRIBUTING. Far too broad; blocks legitimate docs, notes, and
     fixtures.

The salvageable intent (secret scanning, prettier/tsc on edit, console.log warnings) was
rewritten from scratch as the PowerShell scripts above.
