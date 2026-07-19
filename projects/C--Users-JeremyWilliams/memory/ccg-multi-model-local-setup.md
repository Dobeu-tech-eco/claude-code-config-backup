---
name: ccg-multi-model-local-setup
description: ccg-workflow provisioned on Windows; multi-model routing = Claude frontend + Codex backend; Gemini free-tier CLI is dead.
metadata: 
  node_type: memory
  type: project
  originSessionId: 9eff580b-7494-42cf-95db-286f0966cbb2
  modified: 2026-07-19T21:36:53.700Z
---

`ccg-workflow` v3.2.3 provisioned (2026-07-19): `~/.claude/bin/codeagent-wrapper.exe` on User PATH, role prompts in `~/.claude/.ccg/prompts/{codex,gemini,claude,antigravity,grok}/`. Provision non-interactively with `ccg init --skip-prompt --skip-mcp` (bare `npx ccg-workflow` is an interactive TUI that the non-interactive Bash tool force-closes).

**Verified backends (real wrapper round-trips):** codex ✅, claude ✅. **Gemini ❌ — free tier is DEAD:** `IneligibleTierError: UNSUPPORTED_CLIENT` (Google discontinued "Gemini Code Assist for individuals"; pushes to Antigravity). Not fixable ccg-side.

**Routing** in `~/.claude/.ccg/config.toml`: `frontend=claude`, `backend=codex`, `review=[claude,codex]`. `ccg status` confirms Frontend claude / Backend codex.

**ECC `/ecc:multi-*` commands hardcode gemini** for the frontend lane and do NOT read config.toml. When running them, substitute `--backend claude` while keeping the `gemini/frontend.md` / `gemini/reviewer.md` role prompts (they're backend-agnostic). Backend lane = `--backend codex` + `codex/architect.md`. See [[claude-config-restore-2026-07]].

**Adjacent, still unfixed (out of scope of the setup):** `/ccg:spec-review` (`~/.claude/commands/ccg/spec-review.md`) hardcodes `antigravity`; `~/.claude/.ccg/engine/model-router.md` docs still list antigravity as frontend default; orphaned `geminiModel`/`grokModel` keys remain in config.toml (dormant — the review strategy derives reviewers from the frontend+backend lanes, not `routing.review.models`).

**Security note:** wrapper runs codex with `--dangerously-bypass-approvals-and-sandbox` and claude with `--dangerously-skip-permissions`; Code Sovereignty keeps Claude the sole filesystem writer (external calls emit diffs only). Backup of pre-edit config at `config.toml.bak`.
