# P8 — Research (workflow / CI-CD / production path)

## Goal

Parallel research to inform decomposition and the master plan — no implementation.

## Steps

1. Fan out (or sequential if degraded) research tracks:
   - Current CI/CD (GitHub Actions, Replit, Vercel, none)
   - Deploy path vs end-state (preview → prod)
   - Env / secrets / runtime (Node version, Postgres, OpenAI stubs)
   - Quality gates present vs required (`typecheck`, `build`, future tests)
   - Security / compliance constraints from repo rules
2. Write concise notes under `.agent/research/` (or single `.agent/research.md`).
3. Cite sources (files, URLs, MCP). Prefer repo facts over speculation.

## STOP / CONTINUE

- **STOP:** No research artifact written.
- **CONTINUE:** Research notes cover CI/CD + deploy + gates at minimum.

## Outputs

- `.agent/research.md` or `.agent/research/*`
