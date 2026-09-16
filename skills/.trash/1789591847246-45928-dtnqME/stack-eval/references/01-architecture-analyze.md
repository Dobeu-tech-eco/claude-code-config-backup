# P1 — Architecture analyze

## Goal

Produce a grounded architecture snapshot of the current repo relative to the recorded end-state.

## Preferred path (Opsera)

1. Discover Opsera MCP tools (architecture-analyze / equivalent 3-pass analysis + report-telemetry).
2. If server status is `needsAuth` or call fails with auth error → call `mcp_auth` **once** for that server.
3. On success → run 3-pass architecture analysis, report telemetry, write `.agent/architecture.md`.
4. Tag `arch_source: opsera`.

## Local fallback (mandatory if Opsera unavailable)

If Opsera remains unavailable after one auth attempt (or MCP status is error and auth does not fix it):

1. Read `CLAUDE.md` / `AGENTS.md` / `replit.md` as available.
2. Map workspace packages (`pnpm-workspace.yaml`, `artifacts/*`, `lib/*`).
3. Read `lib/api-spec/openapi.yaml` and `artifacts/api-server/src/routes/` (or equivalent API surface).
4. Note SPA entrypoints, DB schema location, env contract.
5. Write `.agent/architecture.md` with the same section shape as an Opsera report would use.
6. Tag **`arch_source: local-fallback`** prominently at the top of the file.

Do **not** block the rest of `/stack-eval` on Opsera.

## STOP / CONTINUE

- **STOP:** Neither Opsera nor local fallback produced `.agent/architecture.md`.
- **CONTINUE:** Architecture note written with `arch_source` tagged.

## Outputs

- `.agent/architecture.md` (`arch_source: opsera | local-fallback`)
