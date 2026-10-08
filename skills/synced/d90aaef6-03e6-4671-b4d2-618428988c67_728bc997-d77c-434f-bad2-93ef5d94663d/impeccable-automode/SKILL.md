---
name: "impeccable-automode"
description: Orchestrates the Impeccable design toolkit (impeccable.style). Invoke when you want a guided, context-aware design pass but do not know which Impeccable command to run. Reads the current conversation, the project's Impeccable context files, and the live state of the work, diagnoses the design situation, then proposes an ordered sequence of real Impeccable commands with reasoning and waits for approval before running anything. Use for "run impeccable automode", "do a full design pass", "which impeccable command should I use", or when design quality is the goal but the specific pass is unclear.
---

# Impeccable Automode

Impeccable ships no automatic mode. It is deliberately a set of focused,
single-purpose commands you run one at a time, reviewing between passes. This
skill supplies the missing orchestration layer: it diagnoses the situation and
sequences the *real* commands for you — it never invents commands and never
runs a destructive or externally visible pass without approval.

## Operating rule

**Propose, then run.** Diagnose → present an ordered plan with reasoning →
get explicit approval → execute one pass at a time → report findings and the
recommended next step after each. Do not batch-run the whole sequence silently.
A single pass may be executed once the plan is approved; after each pass, pause
and report before the next, because Impeccable's passes are dependent (you audit
before you fix, critique before you refine) and a human decision belongs between
stages.

## Step 1 — Gather context before diagnosing

Do these reads first. Do not ask the user for anything that is already here.

1. **The conversation.** What is the user building or fixing? New work or an
   existing page? What have they already said feels wrong?
2. **Impeccable context files**, if present in the repo:
   `PRODUCT.md` (audience + goals), `DESIGN.md` (the visual system), and any
   page briefs. These are the source of truth for the project's intent. If
   `PRODUCT.md` is missing, the project was never initialized — recommend
   `/impeccable init` as step zero.
3. **The current state of the work** — the files or the rendered page the pass
   will act on. Open them; do not assume.

If, after these reads, scope is still genuinely ambiguous (new vs. improve, or
which page), ask one focused question. Otherwise proceed.

## Step 2 — Classify the situation

Map what you found to one of these intents. The intent selects the command
family; the specifics select the command.

| If the goal is… | Lead family | Likely commands |
|---|---|---|
| Make something that does not exist yet | Create | `shape` → `impeccable` |
| Find out what is wrong before fixing | Evaluate | `audit` (implementation) or `critique` (design) |
| Improve a design that basically works | Refine | `polish`, `layout`, `typeset`, `colorize`, `bolder`, `quieter`, `delight`, `animate`, `overdrive` |
| Reduce clutter / confusion | Simplify | `distill`, `clarify`, `adapt` |
| Make it robust for real use | Harden | `harden`, `onboard`, `optimize`, `polish` |
| Capture or reuse the system | System | `document`, `extract`, `generate`, `init`, `live` |

See `reference/commands.md` for the full what/when of all 24 commands. Never
cite a command that is not in that file.

## Step 3 — Build the ordered plan

Chain commands into a sequence that respects Impeccable's natural order:
**evaluate before you change; change before you harden; capture at the end.**

Two canonical backbones:

- **New work:** `shape` (brief) → `impeccable` (build) → `critique` (review) →
  one or more Refine passes → `harden`/`onboard` → `document`.
- **Improve existing:** `critique` *or* `audit` (diagnose) → targeted Refine or
  Simplify passes in priority order → re-`critique` to confirm → `document` if
  the system changed.

Rules for a good plan:

- **Diagnose first.** If no evaluation pass has run this session, the plan
  starts with `critique` (design) or `audit` (implementation), not a fix.
- **One concern per pass.** Do not fold `layout` + `colorize` + `typeset` into
  one step; order them and let the user see each result.
- **Stop at enough.** Do not append `overdrive` or `delight` unless the user
  asked for more presence. Match effort to the request.
- **Capture only if warranted.** `document`/`extract` belong at the end *only*
  when the pass established reusable rules or components.

## Step 4 — Present the plan and get approval

Output, concisely:

1. **Diagnosis** — what you observed, in two or three sentences. Separate fact
   (what the files/context show) from inference (what you suspect is wrong).
2. **Proposed sequence** — the ordered commands, each with one line of why and
   what it will touch.
3. **Stop points** — where you will pause for review.
4. **One recommended first command** to approve.

Then wait. Do not run a pass until the user approves it.

## Step 5 — Execute and report

Run the approved command. After it completes:

- State what changed and what it touched.
- Give the detector/critique findings if the pass produced them.
- Recommend the single best next command, or state that the sequence is done.
- Re-pause for approval before the next pass.

## Guardrails

- **Never invent an Impeccable command.** The real set is the 24 in
  `reference/commands.md`. There is no `automode`, `autofix`, or `all` command.
- **Respect the sequence.** Do not skip the evaluation step to jump to a fix.
- **Approval gates** apply to anything that rewrites files, changes the rendered
  page, or runs a browser/live pass. Read-only passes (`audit`, `critique`,
  `document` of existing state) can proceed once the overall plan is approved.
- **Honor project context over defaults.** If `DESIGN.md` sets a rule and a
  generic design instinct conflicts with it, the project file wins — surface the
  conflict rather than overriding silently.
- **Do not initialize without saying so.** If `PRODUCT.md` is absent, propose
  `/impeccable init` and explain why; do not fabricate audience or goals.

## Notes on invocation

In most agents the underlying commands are `/impeccable …` (e.g.
`/impeccable polish the pricing page`). In Codex they are `$impeccable`. This
skill proposes the commands; the user (or the agent, once approved) issues them
in whichever form their tool uses.
