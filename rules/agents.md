# Agent Orchestration

See also: **startup.md** for the session boot sequence and agent routing table.

<!-- review: 2026-09-09 — removed the swarm/memory/cost plugin layer (purged from config) -->

## The roster is layered — invoke the right layer

Agents come from four layers. Bare names resolve to the flat `~/.claude/agents/` set; plugin agents are prefixed (`ecc:`, etc.). Bare and prefixed names do NOT collide.

| Layer | Owns | Invoke as |
|-------|------|-----------|
| Built-in | broad search / planning primitives | `Explore`, `Plan`, `general-purpose` |
| **Flat `~/.claude/agents/`** | implementers + rich generalists (below) | bare name |
| `ecc:*` (67 agents) | language-specific **review** + **build-fix** + specialists | `ecc:rust-reviewer`, `ecc:java-build-resolver`, … |
| codex/gemini/grok, magic-codex, vercel, ops, oh-my-claudecode | second-opinion, deploy, ops, orchestration | `codex:codex-rescue`, `oh-my-claudecode:executor`, … |

**Ownership rule:** flat keeps only what plugins don't provide. Never recreate a language reviewer/build-resolver flat — delegate to `ecc:*`. Never recreate swarm coordination flat — delegate to `oh-my-claudecode:*`.

## Flat agents (`~/.claude/agents/`)

**Implementers (`*-pro`) — unique to the flat layer; `ecc:*` has no implementers:**
`golang-pro`, `python-pro`, `typescript-pro`, `react-pro`, `nextjs-pro`, `frontend-developer`

**Rich generalists (flat fork is deliberately more detailed than the `ecc:` namesake — flat is canonical, `ecc:` is fallback):**
`security-reviewer`, `e2e-runner`, `build-error-resolver`, `doc-updater`, `refactor-cleaner`

**Other flat:**

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| planner | Implementation planning | Complex features, refactoring |
| architect | System design | Architectural decisions |
| tdd-guide | Test-driven development | New features, bug fixes |
| code-reviewer | Code review | After writing code |
| agent-organizer | Multi-agent orchestration | Tasks spanning many domains |
| api-designer / api-documenter | API design / docs | REST/GraphQL/gRPC endpoints |
| database-migrator | Schema migrations | Database changes |
| docker-specialist | Containerization | Docker/compose setup |
| ci-cd-generator | CI/CD pipelines | GitHub Actions, deployment |
| deployment-engineer | Release management | Production deployments |
| backend-architect / fullstack-architect / cloud-architect | Architecture lanes | Backend / end-to-end / cloud design |
| infrastructure-engineer | Cloud infrastructure | AWS/GCP/Azure setup |
| integration-tester / test-automator | Integration & test automation | API/service testing, coverage |
| performance-engineer | Performance analysis | Profiling, optimization |
| accessibility-auditor | A11y compliance | WCAG audits, fixes |
| **automation-architect** | Composio/Make/Rube tool-routing + cross-system automation | Any task spanning 2+ external systems |
| **memory-curator** | Native file-memory hygiene (dedup/prune/index) | Capture a durable learning; memory audits |

> **CCG is not installed here (verified 2026-09-09).** There is no `agents/ccg/` subdir, no
> `commands/ccg/`, and no `skills/ccg/` on either the Windows or WSL side, so the `/ccg:*` toolchain
> and its agents (`init-architect`, `team-architect`, `team-qa`, `team-reviewer`, `ccg-planner`)
> do not resolve. Use `oh-my-claudecode:*` for orchestration and `ecc:*` for language review instead.

> Removed from this table in the 2026-07-18 reconciliation because they are **archived, not flat**: `deployment-manager` → use `deployment-engineer`; `performance-tester` → `performance-engineer`; `unit-test-generator` → `test-automator` / `integration-tester`.

## Immediate Agent Usage

No user prompt needed:
1. Complex feature requests - Use **planner** agent
2. Code just written/modified - Use **code-reviewer** agent
3. Bug fix or new feature - Use **tdd-guide** agent
4. Architectural decision - Use **architect** agent
5. Build failure - Use **build-error-resolver** agent
6. Security-sensitive change - Use **security-reviewer** agent

## Parallel Task Execution

ALWAYS use parallel Task execution for independent operations:

```markdown
# GOOD: Parallel execution
Launch 3 agents in parallel:
1. Agent 1: Security analysis of auth.ts
2. Agent 2: Performance review of cache system
3. Agent 3: Type checking of utils.ts

# BAD: Sequential when unnecessary
First agent 1, then agent 2, then agent 3
```

## Multi-Perspective Analysis

For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker
