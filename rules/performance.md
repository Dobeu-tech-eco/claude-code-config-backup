# Performance Optimization

## Model Selection Strategy

Current lineup: the **Claude 5 family** (Fable 5, Sonnet 5), **Opus 4.8**, and **Haiku 4.5**.
Default new AI-application work to the latest, most capable models. (The old 4.5 tiers —
"Sonnet 4.5 / Opus 4.5" — are superseded; do not route to them.)

**Haiku 4.5** (fast, low-cost; ~90% of a mid-tier model's capability):
- Lightweight agents with frequent invocation
- Pair programming and code generation
- Worker agents in multi-agent systems

**Sonnet 5 / Fable 5** (strong general coding + orchestration):
- Main development work
- Orchestrating multi-agent workflows
- Complex coding tasks

**Opus 4.8** (deepest reasoning):
- Complex architectural decisions
- Maximum reasoning requirements
- Research and analysis tasks

> Note: Fast mode for Claude Code uses Opus with faster output (not a smaller model);
> toggle with `/fast` on Opus 4.8/4.7.

## Context Window Management

Avoid last 20% of context window for:
- Large-scale refactoring
- Feature implementation spanning multiple files
- Debugging complex interactions

Lower context sensitivity tasks:
- Single-file edits
- Independent utility creation
- Documentation updates
- Simple bug fixes

## Ultrathink + Plan Mode

For complex tasks requiring deep reasoning:
1. Use `ultrathink` for enhanced thinking
2. Enable **Plan Mode** for structured approach
3. "Rev the engine" with multiple critique rounds
4. Use split role sub-agents for diverse analysis

## Build Troubleshooting

If build fails:
1. Use **build-error-resolver** agent
2. Analyze error messages
3. Fix incrementally
4. Verify after each fix
