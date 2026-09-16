# The three-agent harness — planner, generator, evaluator

Anthropic's published April 2026 work on long-running agent harnesses is direct: even a frontier model on the Agent SDK in a loop falls short of producing a production-quality web app from a high-level prompt. What works is a three-agent architecture that separates *deciding what to do*, *doing it*, and *checking it*.

This skill encodes that pattern.

## Why three agents

A single agent doing everything has three failure modes:

1. **Context bloat**: planning, generating, and verifying all share the same context window. The window fills, the model gets cautious, quality drops.
2. **Self-evaluation blindness**: an agent that just wrote code is the worst judge of whether the code is correct. It has the *intent* in its head, not the *result*.
3. **No checkpoint signal**: with one continuous stream there's no natural moment to write a state snapshot, commit, or hand off.

Splitting into planner + generator + evaluator solves all three:

- Each agent runs in a clean (or near-clean) context.
- The evaluator reads the generator's output cold — same eyes the user will eventually use.
- The boundaries between agents are natural checkpoint moments.

## Roles

### Planner

**Model:** Sonnet (sometimes Opus for high-stakes architecture).
**Inputs:** User idea, current `tasks.json` if mid-build, any constraints / preferences.
**Outputs:** Updated `tasks.json` with feature list, risk register, scope decision, and stack choice if not yet locked.
**Returns to orchestrator:** ~600–1,200 token plan summary.

The planner runs as a subagent so its exploration (reading docs, weighing trade-offs, pricing options) doesn't pollute the orchestrator's context. The orchestrator gets the distilled output, presents it to the user, and waits for sign-off.

Planner prompt template:

```
You are the planner. The user wants: <idea>.
Current state: <relevant excerpts from tasks.json + state.json, or "blank slate">.
Constraints: <budget, deadline, stack preferences, integrations connected>.

Produce:
1. One-paragraph problem statement (who, what, why).
2. MVP scope — the smallest demonstrable version.
3. Stack decision with one-sentence rationale per choice.
4. Feature list (≤8 features), each with 3–6 implementation steps and a difficulty rating (S/M/L).
5. Risk register: top 5 things that could go wrong, mitigation per item.
6. Phase ordering: which features are foundation (Phase 2) vs build-out (Phase 3).

Return as JSON conforming to .agent/tasks.json schema. Be concrete, opinionated, and brief.
```

### Generator

**Model:** Sonnet by default; Haiku for trivial features; Opus for hard refactors.
**Inputs:** One feature from `tasks.json` (with all its steps), the current repo state, the test harness.
**Outputs:** Code, tests, commits, an updated `tasks.json` (status / passes only).
**Returns to orchestrator:** "Done" + commit SHA + test results, or "Blocked" + reason.

The generator works one feature at a time. It does *not* re-plan, does *not* skip ahead, does *not* edit the feature description. Discipline is the whole point.

Generator prompt template:

```
You are the generator. Implement feature <id>: <description>.
Steps:
<steps from tasks.json>

Workflow:
1. Mark feature in_progress in tasks.json (status only — descriptions are immutable).
2. Write a failing test that captures the feature's intent.
3. Implement the feature in the smallest commits possible. Commit format: [CATEGORY] description.
4. Run lint, typecheck, build, tests. All must pass.
5. Mark passes: true ONLY if the verification gate is green.
6. Append a one-line entry to .agent/progress.md.

If you get stuck on a sub-step, don't escalate scope — return "Blocked" with the reason and the last green commit SHA.
```

### Evaluator

**Model:** Haiku or Sonnet (clean context is more important than capability here).
**Inputs:** Recent commits (last 1–3 features' worth), `tasks.json`, key files (entry points, schema).
**Outputs:** A 200–400 word report flagging anything that needs attention.
**Returns to orchestrator:** Findings list, with severity (P1/P2/P3) per item.

The evaluator runs after every 2–3 generator features, or before any major checkpoint (deploy, merge, release). It does not write code; it reads, runs the test suite, exercises the deploy preview, and reports.

Evaluator prompt template:

```
You are the evaluator. The generator has shipped these commits: <git log --oneline since last evaluator run>.

Verify:
1. Tests cover the new code paths (run the test suite, report coverage delta).
2. Types are sound (run typecheck, report errors).
3. Foundation flows still work (run smoke tests against the deploy preview if available).
4. Integrations still respond (one-call health check against each connected Composio integration).
5. No secrets in the diff (run gitleaks or equivalent).
6. README and docs are current relative to the new code.

Return: ≤400 words, findings list with severity. Be specific (file:line where possible).
P1 = blocks ship. P2 = needs fix this phase. P3 = note for backlog.
```

## When to compact, when to reset

Anthropic's harness work draws a distinction between *compacting* context (preserving information but condensing it) and *resetting* context (starting fresh, with a structured handoff artifact bridging the boundary).

For this pipeline:

- **Within a single agent's turn:** compact. `/compact` at 50% fill keeps the agent productive without losing thread.
- **Between phases:** reset. The generator finishes Phase 2 → write `progress.md` and `state.json` → start Phase 3 with a fresh context, reading those artifacts as the only carry-forward.
- **Between agent roles:** reset. The planner doesn't share context with the generator; the generator doesn't share context with the evaluator. Each gets a tight role-specific prompt and reads `.agent/` files for state.

## Subagent budget

Workers (subagents) are cheap on Haiku and trivially parallelizable. Use them aggressively for:

- "Read these 8 files and summarize what each does" → 1 subagent, 1 summary back.
- "Check whether library X has a function Y" → 1 subagent.
- "Try this fix in a worktree and run tests" → 1 subagent per worktree, parallel.
- "Read the docs for these 3 APIs" → 3 parallel subagents.

Don't use a subagent for:

- A single file read you can do directly.
- A decision you need to make yourself (subagents don't share your full intent).
- Anything where you need the full file contents back, not a summary.

## Failure cases for the harness itself

- **Planner over-plans.** Cap at 8 features; if the planner returns 20, push back and have it fold into MVP vs backlog.
- **Generator silently changes scope.** Watch for diffs that touch files outside the feature's stated steps. Stop and re-plan.
- **Evaluator rubber-stamps.** If three runs in a row return "all clear," check the prompt — the evaluator is probably not exercising the deploy preview. Be specific in the prompt.
- **Orchestrator forgets to checkpoint.** Set a hard rule: after every evaluator run, write `state.json` and commit. No exceptions.

## Sources

- [Effective harnesses for long-running agents — Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Anthropic designs three-agent harness for long-running full-stack AI development — InfoQ (April 2026)](https://www.infoq.com/news/2026/04/anthropic-three-agent-harness-ai/)
- [Effective context engineering for AI agents — Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Harness design for long-running application development — Anthropic](https://www.anthropic.com/engineering/harness-design-long-running-apps)
