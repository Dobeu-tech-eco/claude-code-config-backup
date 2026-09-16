# Output formats and runtime compatibility

The exporter emits one bundle that four runtimes can each consume from their
own preferred surface. Nothing is runtime-specific in a lossy way — the same
skills appear in every surface, just shaped differently.

## Codex (and other AGENTS.md agents) — `AGENTS.md`

OpenAI Codex and compatible agents read an `AGENTS.md` instructions file from
the project root. The exporter's `AGENTS.md` is, by default, a **catalog**: a
header telling the agent these are available skills, then one bullet per skill
with its origin, a one-line *when to use*, and a pointer to
`skills/<name>/SKILL.md`. This is deliberate progressive disclosure — a 900-skill
bundle with every body inlined would be multiple megabytes and overflow the
agent's context. The agent loads a skill's full instructions from its folder
only when a request matches.

Use `--inline-agents` if the user specifically wants every skill body inside
`AGENTS.md` (large file; only sensible for small skill sets).

## Claude / skills.sh — `skills/<name>/SKILL.md`

Each skill is emitted as an individual folder containing a `SKILL.md` with valid
frontmatter: `name` (lowercase-hyphen, equal to the folder name) and
`description`. An `metadata.origin` line records where it came from. This is
exactly the shape:

- Claude reads directly (personal or plugin skills).
- skills.sh packs accept as uploaded files/folders/zip, or from a GitHub repo.

The bodies are the skills' original instructions, unmodified.

## One combined file — `skills.md`

`skills.md` is the single "everything in one file" artifact: a catalog table of
all skills, followed by each skill's full instructions inlined under its own
heading with origin and source pointer. This is what to hand someone who asked
to "combine all my skills into one file".

## v0.app — `v0/skills-list.md`

v0.app attaches skills to a prompt using only their `name` + `description`; it
has no shell, MCP, or filesystem beyond the generated project. `v0/skills-list.md`
is a name + description table for exactly that. Instruction-only skills (design
systems, UI/UX guidance, copy, SEO) work as-is on v0. Skills that depend on a
shell, MCP tools, external CLIs, or `/mnt/...` paths will not *execute* on v0,
but their written guidance can still inform the generated code — the list does
not filter them out, so the user chooses per prompt.

## manifest.csv

Columns: `name, slug, origin, status, valid_name, source_path, description`.
`status` is `included` or `duplicate_shadowed_by:<origin>`. `origin` is
`personal` or `plugin:<plugin-name>`. Use it to audit what was combined and what
was shadowed by a same-named skill.

## Notes on safety and size

- The script reads only `SKILL.md` text files. It never copies binaries or
  bundled assets, so the bundle carries no large or opaque files.
- Nothing is uploaded anywhere; the export is entirely local and produces a
  single `.zip` for the user to place where they want.
- Same-named skills are de-duplicated (personal over plugin, earlier source
  over later); shadowed copies are recorded, not silently dropped.
