---
name: skills-exporter
description: Combine every skill an AI agent can access into one portable, multi-agent bundle and produce a downloadable .zip. Use this skill whenever the user wants to export, combine, bundle, back up, share, or migrate their skills — including any request to "put all my skills into one skills.md", "export my skills to Codex / AGENTS.md", "make a skills.zip", "bundle my skills for v0.app", "combine all skills into one file", "give me a downloadable copy of my skills", or move skills between Codex, Claude, skills.sh, and v0.app. The bundle contains a single combined skills.md index, a Codex-compatible AGENTS.md, individual per-skill SKILL.md folders (Claude / skills.sh layout), a v0.app name+description list, and a manifest.csv — delivered as one .zip.
metadata:
  author: Dobeu Tech Solutions LLC
  version: 1.0.0
---

# Skills Exporter

Discover every skill the current agent can reach, combine them into **one
`skills.md`** plus the file structures other agent runtimes expect (Codex,
Claude / skills.sh, v0.app), and hand the user a downloadable `.zip`.

Use this whenever someone wants to export, back up, share, migrate, or combine
their skills — even if they don't say "export" (e.g. "put all my skills in one
file", "make an AGENTS.md from my skills", "bundle these for v0").

## What it produces

Running `scripts/export_skills.py` writes an output folder and zips it. The zip
contains:

- **`skills.md`** — the single combined index of every skill: a catalog table
  plus each skill's full instructions inlined. This is the "one file with
  everything" deliverable.
- **`AGENTS.md`** — Codex-compatible entry point. By default it is a catalog of
  every skill with a one-line *when to use* and a pointer to the skill's folder
  (progressive disclosure), so it stays small enough for Codex to load. The
  bodies live in `skills/<name>/SKILL.md` and `skills.md`. (Use `--inline-agents`
  only if the user explicitly wants every body inside AGENTS.md.)
- **`skills/<name>/SKILL.md`** — each skill as an individual folder in the
  Claude / skills.sh format (valid `name` + `description` frontmatter). This is
  what skills.sh packs and Claude read directly.
- **`v0/skills-list.md`** — a name + description table for attaching skills in
  v0.app (v0 uses only name + description).
- **`manifest.csv`** — every skill's name, slug, origin (personal vs
  `plugin:<name>`), dedup status, source path, and description.
- **`README.md`** — what's inside and how to regenerate.

## How to run it

The script is pure standard library (no pip installs) and auto-discovers skill
sources. From the skill directory:

```bash
python3 scripts/export_skills.py --out ./skills-export --zip ./skills-export.zip
```

Then deliver `skills-export.zip` to the user (in Cowork, use the file-delivery
tool; on other harnesses, tell the user the path).

### Discovery

With no `--src`, it scans the first existing of each: `~/.claude/skills/synced`,
`~/.claude/skills`, `~/.claude/plugins/synced/*/skills`,
`~/.claude/plugins/*/skills`, `./.claude/skills`, `./skills`, and any roots in
`$CLAUDE_SKILLS_PATH`. Point it elsewhere with repeatable `--src <dir>`, where
`<dir>` directly contains `<skill>/SKILL.md` folders. A "skill" is any directory
whose `SKILL.md` has YAML frontmatter with at least a `name`.

### Dedup and origins

Skills are de-duplicated by name. Personal skills win over plugin skills;
earlier sources win over later. Shadowed duplicates are still recorded in
`manifest.csv` with a `duplicate_shadowed_by:<origin>` status, so nothing is
silently dropped — report the duplicate count to the user.

### Useful flags

- `--index-only` — `skills.md` / `AGENTS.md` list descriptions only (no bodies).
  Good for a quick catalog when the user only wants the list.
- `--inline-agents` — inline full skill bodies into `AGENTS.md` too (large;
  only when explicitly requested).
- `--no-zip` — write the folder but skip zipping.
- `--src <dir>` — add a source root (repeatable).

## Working with the user

1. Run the export with defaults first, then tell the user the counts: how many
   skills were combined and how many duplicates were shadowed.
2. Deliver the `.zip`, and name the four target runtimes it covers (Codex via
   `AGENTS.md`, Claude / skills.sh via `skills/<name>/`, one combined
   `skills.md`, v0.app via `v0/skills-list.md`).
3. If the user names a specific target (e.g. "just for Codex" or "just one
   file"), point them at the relevant artifact rather than re-running.

See `references/formats.md` for how each runtime consumes the output and the
compatibility notes (what works instruction-only vs. needs tools).

## Verify before reporting done

After running, confirm the deliverable is real, not assumed:

- The `.zip` exists and is non-empty (`unzip -l` shows `skills.md`, `AGENTS.md`,
  `manifest.csv`, and `skills/` folders).
- The manifest row count matches the number of skills the environment actually
  has (spot-check against the source directories).
- Optionally validate the emitted `skills/` folders: each `SKILL.md` starts with
  `---`, has `name` matching its folder, and a `description`.
