# P2 — GitHub code review

## Goal

Capture open-PR review signal when available; never block planning on GitHub/MCP failure.

## Steps

1. Detect `.git` and remote. If missing → **skip** with reason in `.agent/code-review.md`.
2. If open PR exists (`gh pr view` / GitHub MCP):
   - Prefer project skill `github-code-review` / `gh` PR review + optional review swarm.
   - Summarize findings into `.agent/code-review.md`.
3. If no open PR → skip with reason (`no open PR`).
4. If GitHub MCP fails → fall back to `gh` CLI; if that fails → skip with reason. Tag `review_source: skipped|gh|mcp`.

## STOP / CONTINUE

- **STOP:** Never — this phase must not block the pipeline.
- **CONTINUE:** Always after writing skip reason or review summary.

## Outputs

- `.agent/code-review.md`
