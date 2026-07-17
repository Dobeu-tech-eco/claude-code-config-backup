# Plan: Provision the `ccg-workflow` runtime for `/ecc:multi-execute`

## Context

The `/ecc:multi-execute` and `/ecc:multi-plan` commands route implementation
work through external models (Codex/Gemini) that emit Unified Diff patches,
which Claude then refactors and applies (Claude stays the only filesystem
writer). Both commands depend on an external runtime, `ccg-workflow`, that is
**not** part of the base ECC install.

A verification probe run earlier reported the runtime missing. A full
dependency-tree debug (this session) confirmed the root cause and, importantly,
that provisioning is **unblocked**: every upstream dependency is already
present and healthy — only the two artifacts that `npx ccg-workflow` itself
creates are absent.

### Dependency debug results

| Dependency | Role | Status |
|-----------|------|--------|
| node / npm / npx (v24.18.0 / 12.0.1) | runs the provisioner | ✅ present |
| `codex` CLI (0.144.3) | backend the wrapper calls | ✅ present |
| `gemini` CLI (0.50.0) | backend the wrapper calls | ✅ present |
| `ccg-workflow` npm pkg (v3.2.3) | the provisioner | ✅ on registry |
| `~/.claude/bin/codeagent-wrapper` | entrypoint every model call invokes | ❌ missing |
| `~/.claude/.ccg/prompts/{codex,gemini}/*.md` | role files (analyzer, architect, frontend, reviewer) | ❌ missing |
| `ace-tool` MCP | optional context accelerator | ⚪ optional — built-in fallback exists |

**Outcome intended:** a single provisioning run creates the wrapper + role
files, after which `/ecc:multi-plan` and `/ecc:multi-execute` are usable.

## Approach

Run the official provisioner, then re-run the exact probe from the earlier
output to confirm both misses are resolved.

### Step 1 — Provision

```bash
npx ccg-workflow
```

Run through the **Bash (Git Bash)** tool, not PowerShell — the wrapper installs
to `~/.claude/bin/` and the command specs use POSIX heredocs (`<<'EOF'`), so the
whole workflow assumes a POSIX shell. If the provisioner prompts interactively,
surface the prompt to the user rather than guessing answers.

Expected artifacts created:
- `~/.claude/bin/codeagent-wrapper` (the entrypoint)
- `~/.claude/.ccg/prompts/codex/{analyzer,architect,reviewer}.md`
- `~/.claude/.ccg/prompts/gemini/{analyzer,architect,frontend,reviewer}.md`

### Step 2 — Verify (re-run the original probe)

```powershell
$w = 'C:\Users\JeremyWilliams\.claude\bin\codeagent-wrapper'
$p = 'C:\Users\JeremyWilliams\.claude\.ccg\prompts'
[pscustomobject]@{
  wrapper_exists  = (Test-Path $w) -or (Test-Path "$w.cmd") -or (Test-Path "$w.ps1")
  wrapper_matches = (Get-ChildItem 'C:\Users\JeremyWilliams\.claude\bin' -Filter 'codeagent-wrapper*' -EA SilentlyContinue | Select-Object -Expand Name) -join ', '
  ccg_prompts_dir = Test-Path $p
  prompt_files    = (Get-ChildItem $p -Recurse -File -EA SilentlyContinue | Select-Object -Expand FullName) -join '; '
} | Format-List
```

**Pass criteria:** `wrapper_exists = True`, `ccg_prompts_dir = True`, and
`prompt_files` lists the codex/gemini role `.md` files.

## Verification

- Re-running the probe above returns `True` for wrapper + prompts dir and a
  non-empty `prompt_files` list. (The backends — `codex` 0.144.3, `gemini`
  0.50.0 — are already confirmed responding, so no separate backend check is
  needed for the "provision + verify" scope.)

## Out of scope / notes

- No end-to-end wrapper round-trip (a full `codeagent-wrapper --backend codex …`
  call) — that was the "provision + smoke test" option, not chosen here.
- `ace-tool` MCP is intentionally left unconfigured; both commands fall back to
  Glob/Grep/Read/Explore when it is absent.
- Separately noted from prior context: the *current* work (config edits, moving
  ~89 files, git init) is a poor fit for multi-execute regardless — this plan
  only makes the runtime available for future frontend/backend tasks.
