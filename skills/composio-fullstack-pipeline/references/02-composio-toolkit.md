# Composio toolkit — the integration spine

Composio's job in this pipeline is simple: it is the universal adapter between the agent and the outside world. The agent writes code locally; Composio executes everything else — creating repos, opening PRs, deploying previews, querying databases, filing issues, running campaigns.

## Why Composio (not direct API calls)

Three reasons:

1. **Auth is centralized.** The user authenticates once per app via Composio's OAuth flow; the agent never holds raw API keys. This eliminates an entire class of leak risk.
2. **Schemas are uniform.** Every integration speaks the same call shape, so the agent doesn't need to learn N different SDK quirks.
3. **Bulk execution is cheap.** `COMPOSIO_MULTI_EXECUTE_TOOL` runs N independent calls in parallel server-side, returning one consolidated response. Genuinely independent work that would burn 8–10 sequential round-trips becomes 1.

## The five tools that matter

| Tool | When to use |
|---|---|
| `COMPOSIO_MANAGE_CONNECTIONS` | Session start (catalog) and any time a needed app isn't connected. |
| `COMPOSIO_SEARCH_TOOLS` | Discover the right action for a task — e.g., "create a Vercel preview deployment." |
| `COMPOSIO_GET_TOOL_SCHEMAS` | Load the schema for a specific action before invoking it. |
| `COMPOSIO_MULTI_EXECUTE_TOOL` | Batch independent actions (parallel). |
| `COMPOSIO_REMOTE_BASH_TOOL` / `COMPOSIO_REMOTE_WORKBENCH` | Run scripts in an isolated cloud sandbox when local execution is risky or impossible. |

## MCP vs SDK vs API — decision tree

```
Task involves an external system?
├── Native MCP for that exact app is connected?
│    └── Yes → use it (lowest latency, richest schema)
├── 2+ apps in one workflow OR app has no native MCP?
│    └── Yes → Composio
├── Bulk parallel work or sandboxed script execution?
│    └── Yes → Composio multi-execute or remote workbench
├── Webhook / scheduled / event-driven workflow?
│    └── Yes → Composio triggers (or Make.com if scenario logic is needed)
└── Local file / repo / shell?
     └── Bash / Read / Edit / Write — never round-trip to Composio for these
```

The general rule: **MCP for single-app actions, Composio for cross-system orchestration, shell for local work.** Don't recreate with shell scripting what an MCP can do reliably; don't round-trip to Composio for `git status`.

## Top integrations for a full-stack build

For each of the integrations below, Composio exposes 30–80+ actions. The list here is the *most-used* per integration — use `COMPOSIO_SEARCH_TOOLS` to find others.

### GitHub
- `create_repository`, `create_branch`, `create_pull_request`, `merge_pull_request`
- `create_or_update_file`, `get_file_contents`, `list_commits`
- `create_issue`, `add_comment_to_issue`
- `list_workflow_runs`, `cancel_workflow_run`
- Gotcha: branch protection rules silently block `merge_pull_request` if reviews are required and the agent is the only actor. Surface this to the user before relying on auto-merge.

### Linear
- `create_issue`, `update_issue`, `archive_issue`
- `list_issues`, `get_issue`
- `create_project`, `create_cycle`
- `create_comment`
- Gotcha: Linear team IDs are required for most creates — fetch once at session start and cache in `state.json`.

### Vercel
- `create_project`, `link_project_to_repo`
- `create_deployment`, `list_deployments`, `cancel_deployment`
- `list_environment_variables`, `create_environment_variable`
- `add_domain_to_project`, `list_dns_records`
- `read_deployment_logs`, `get_runtime_logs`
- Gotcha: env vars must be created per environment (preview, production) separately. The agent should always create both unless the user specifies otherwise.

### Supabase
- `create_project`, `create_branch`, `merge_branch`
- `execute_sql` (read), `apply_migration` (write — DDL only)
- `deploy_edge_function`, `get_logs`
- `get_advisors` — run before any production deploy
- Gotcha: `execute_sql` is read-only by design; DDL goes through `apply_migration` so it's tracked in version control.

### Sentry
- `search_issue_events`, `get_issue_tag_values`
- `get_replay_details`, `get_profile_details`
- Gotcha: source maps must be uploaded during the build step (e.g., via `@sentry/nextjs` Webpack plugin) — if Sentry shows minified stacks, that step is missing.

### PostHog
- Feature flag listing/setting
- Event ingestion verification
- Gotcha: identify the user *before* the first event fires, or the events end up under an anonymous distinct_id and analytics is broken.

### Stripe
- Products, prices, customers, checkout sessions, webhook endpoints
- **Test mode only from an agent.** Live-mode requires explicit user approval each time.
- Gotcha: webhook signing secrets are per-endpoint per-environment. Don't reuse a test webhook secret in production.

### Figma
- Read-only design context (components, variables, screenshots)
- Useful in Phase 1 (planner) when the user has a design and the agent is mapping components to code.

## Multi-execute pattern

When the planner decides "we need a GitHub repo, a Linear project, a Supabase project, and a Vercel project — all empty, all named after the idea," that's four independent calls. Don't loop. One multi-execute:

```json
{
  "tool": "COMPOSIO_MULTI_EXECUTE_TOOL",
  "calls": [
    {"tool": "GITHUB_CREATE_REPOSITORY", "params": {"name": "<idea-slug>", "private": true}},
    {"tool": "LINEAR_CREATE_PROJECT", "params": {"team_id": "<id>", "name": "<idea-name>"}},
    {"tool": "SUPABASE_CREATE_PROJECT", "params": {"name": "<idea-slug>", "region": "us-east-1"}},
    {"tool": "VERCEL_CREATE_PROJECT", "params": {"name": "<idea-slug>", "framework": "nextjs"}}
  ]
}
```

Single round-trip, parallel server-side execution. Returns when all complete (or any fail) with a consolidated result.

Sequential is mandatory only when later steps depend on IDs from earlier steps (e.g., link Vercel to GitHub repo *after* the repo exists).

## Sandboxed execution

When the agent needs to run a build / migration / data transform that's risky to execute locally, use `COMPOSIO_REMOTE_WORKBENCH`:

- Spins up an isolated cloud sandbox (Linux, Python + Node preinstalled).
- Mount the repo (or a subset).
- Run the script.
- Return stdout/stderr.
- Tear down.

This is particularly valuable for: Supabase migration dry-runs, npm install + build verification before pushing, untrusted code from `firecrawl_extract` outputs, anything you'd otherwise be nervous about running directly on the user's machine.

## Safe defaults

- Always pass `idempotency_key` where the action supports it (Stripe, GitHub Issues, Linear).
- Never call a destructive action in multi-execute alongside a creation — separate the batches.
- For any action that sends real-world communication (email, SMS, Slack DM, GitHub @mention of someone other than the user), pause and confirm before invoking.
- Verify connection health at session start. `COMPOSIO_MANAGE_CONNECTIONS` returns each connection's status; expired tokens look healthy until the first call fails.

## Sources

- [Composio docs (root)](https://docs.composio.dev/docs)
- [ComposioHQ/composio on GitHub](https://github.com/ComposioHQ/composio)
- [Composio MCP integration with Claude Code](https://composio.dev/toolkits/composio/framework/claude-code)
- [Composio MCP — toolkits page](https://mcp.composio.dev/composio)
