# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This repo is a **collection of Claude skills** — agent-loadable capability bundles. Each top-level directory is one skill (e.g. `algorithmic-art/`, `pdf/`, `pptx/`, `docx/`, `xlsx/`, `mcp-builder/`, `notebooklm/`, `slack-gif-creator/`, `web-artifacts-builder/`, `theme-factory/`, etc.). Skills are designed to be discovered and invoked at runtime via the host's `Skill` tool — they are not a single application with a build pipeline.

The `skill-creator/` directory is the meta-skill: it contains the tooling used to author, validate, package, and evaluate every other skill in the repo. When working on skills here, you will almost always be using `skill-creator/scripts/*` rather than language-level tooling.

## Skill anatomy

Every skill directory MUST contain a `SKILL.md` with YAML frontmatter:

```
---
name: <kebab-case, must match directory name>
description: <one paragraph — used by the model at runtime to decide whether to load this skill. The wording here is load-bearing; the eval harness measures triggering accuracy against it.>
license: <optional>
---
<skill body in Markdown>
```

Common optional subdirectories inside a skill:
- `scripts/` — Python helpers the skill body tells the agent to run
- `references/` — long reference docs the skill body links to (loaded on demand, not eagerly)
- `assets/` — static files (templates, images, fonts) the skill ships with
- `agents/` — subagent prompts the skill dispatches to (see `skill-creator/agents/`)

Keep `SKILL.md` short and progressive-disclosure: put discovery-relevant guidance up top, push verbose detail into `references/` files that the body links to.

## Common commands (from repo root)

All skill-management scripts live in `skill-creator/scripts/` and are invoked as Python modules so their relative imports resolve. Run them from `skill-creator/`:

```bash
cd skill-creator

# Validate a skill's structure / frontmatter
python -m scripts.quick_validate ../<skill-name>

# Package a skill into a distributable .skill (zip) file
python -m scripts.package_skill ../<skill-name> ./dist

# Run trigger eval — does Claude actually load the skill for these queries?
python -m scripts.run_eval ../<skill-name>

# Aggregate eval results across runs (variance analysis)
python -m scripts.aggregate_benchmark <results-dir>

# Iterate on the description field to improve trigger accuracy
python -m scripts.improve_description ../<skill-name>

# Render an HTML review of an eval run
python eval-viewer/generate_review.py <results-dir>
```

`run_eval.py` walks up from cwd looking for `.claude/` to anchor the project root, so run it from inside the repo.

`slack-gif-creator/` is the one skill with its own Python deps — install via `pip install -r slack-gif-creator/requirements.txt` if working on it. No other skill has a lockfile or package manifest.

## Authoring workflow

When asked to create or modify a skill, invoke the `skill-creator` skill via the `Skill` tool first — it encodes the iterative loop (draft → eval → critique → revise) and is the source of truth for conventions. Do not author a `SKILL.md` from scratch from memory; the format and the description-tuning process are both opinionated.

Rough loop:
1. Draft `SKILL.md` (and any `scripts/`, `references/`, `assets/` it needs).
2. `quick_validate` to catch structural issues.
3. `run_eval` against a small set of trigger prompts to measure whether the description fires correctly.
4. Use `improve_description` and the `eval-viewer` review to tune the `description` field — this is usually where the work is, not in the body.
5. `package_skill` only when shipping.

## Conventions specific to this repo

- **Description field is the product.** It controls whether the skill loads at all. Treat changes to it as a behavior change requiring re-evaluation, not a docs tweak.
- **No global build / lint / test.** Each skill is self-contained. Don't add a root `package.json`, `pyproject.toml`, or CI config unless explicitly asked — it would change the repo's shape.
- **Cross-skill changes are rare.** A single task almost always touches exactly one skill directory plus possibly `skill-creator/`. If you find yourself editing many sibling skills at once, stop and confirm — that is usually a sign of misunderstanding the request.
- **Packaging excludes `evals/` at skill root, plus `__pycache__/`, `node_modules/`, `*.pyc`, `.DS_Store`** (see `EXCLUDE_*` in `package_skill.py`). Eval artifacts stay in-repo for iteration but never ship.
