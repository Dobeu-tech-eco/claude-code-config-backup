---
name: grok-review
description: >-
  Send the current artifact, plan, or piece of work to Grok (a different model
  family) for an independent, adversarial second opinion, then surface Grok's
  review and structured verdict. Use this whenever the user asks for "Grok's
  take", "a second set of eyes", "cross-review with Grok", "have Grok check
  this", "push this to Grok", "what does Grok think", or wants a
  planner/evaluator ensemble where Claude proposes and Grok critiques (or vice
  versa). Trigger it for code, plans, architecture decisions, SOPs, specs, and
  document outlines — even when the user doesn't say the word "skill". Requires a
  Claude Code or Cowork session with the `grok` CLI installed, an XAI_API_KEY, or
  a Composio xAI bridge; it does not run in plain claude.ai chat.
---

# Grok Review

Get an independent critique of your work from Grok. The value is that the
reviewer comes from a *different* model prior, so it catches things a same-model
self-review rubber-stamps. A review that only praises is a failed review — push
for disagreement.

## When this runs vs. when it can't

This skill executes a real call to Grok. That only works where Grok credentials
live: a Claude Code or Cowork session with the `grok` CLI on PATH, an
`XAI_API_KEY` environment variable, or a configured Composio xAI tool. In plain
claude.ai chat there is no Grok access — if asked there, explain that and offer
to draft the review prompt for the user to paste into Grok manually.

## Workflow

1. **Identify the artifact.** Resolve the file(s) under review — the latest
   thing edited, a path the user named, or a plan file. For binary Office files
   (`.docx`/`.xlsx`/`.pptx`), convert to reviewable text first with
   `python scripts/extract_office.py <file> > /tmp/artifact.txt` and pass that —
   both models critique raw binaries poorly. For a higher-level pass, review the
   markdown spec/outline instead of the rendered file.

2. **Write a tight context brief.** One short paragraph: what the artifact is
   for, the constraints that matter, and what kind of review is wanted. Keep the
   author's own conclusion *out* of it when running blind (see below).

3. **Run the review script:**

   ```bash
   python scripts/grok_review.py \
     --artifact path/to/file \
     --context "@path/to/brief.md" \
     --backend auto \
     --blind \
     --out .agent/reviews
   ```

   - `--backend auto` tries `grok` CLI -> `XAI_API_KEY` -> Composio payload, in
     that order. Pin it with `--backend grok-cli|xai-api|composio` when needed.
   - `--blind` strips the author's stated conclusions from the context so Grok
     isn't anchored into agreement. Prefer blind for plan/architecture reviews.
   - Repeat `--artifact` for multiple files.

4. **Surface the result.** Read `.agent/reviews/<timestamp>/review.md` and the
   `verdict.json` if present. Report Grok's verdict (approve / revise / reject),
   its top issues, the one thing it says is wrong, and any simpler alternative.
   Do not soften or filter Grok's critique — relay it straight, then add your own
   brief take on which points you accept or contest.

5. **Synthesize (optional).** If the user wants a merged plan, fold the accepted
   points into a `plan-final.md` with a one-line rationale per change. State
   plainly where you and Grok disagree rather than papering over it.

## The review rubric

The script injects a fixed rubric so Grok returns a scorecard, not vibes:
correctness, completeness, risk, simpler alternative, and the single most
important miss — followed by a JSON verdict block. Keep this rubric stable so
reviews are comparable across runs.

## Cost discipline

A full cross-review roughly doubles planning tokens for a task. Reserve it for
high-stakes work — a compliance SOP, an Auth0 or RAG architecture call, a risky
refactor — and skip it for routine edits. Note in any handoff that a Grok review
was run and where the artifact lives.

## Backends and portability

- `references/backends.md` — install the `grok` CLI, set `XAI_API_KEY`, wire the
  Composio xAI route, and the Bring-Your-Own-MCP path so Grok Build can reach
  your Composio toolkits directly.
- `references/portability.md` — make your existing Claude skills and CLAUDE.md
  visible to Grok Build (and Hermes) so all agents follow the same rules. This is
  the "seamless availability" half of the request.

## Reverse direction

This skill is symmetric in spirit: the same rubric and `.agent/reviews/`
convention work when Grok Build is the author and Claude is the reviewer. In that
case Grok writes its plan to disk and Claude reads and critiques it — no script
needed, just point Claude at the plan file.
