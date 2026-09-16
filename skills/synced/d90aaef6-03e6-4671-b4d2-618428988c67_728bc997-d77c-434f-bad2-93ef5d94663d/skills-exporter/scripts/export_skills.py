#!/usr/bin/env python3
"""
export_skills.py — Discover every skill an AI agent can reach and combine them
into one portable bundle, with file structures for multiple agent runtimes
(Codex AGENTS.md, Claude / skills.sh skills/<name>/SKILL.md, v0.app), plus a
single combined skills.md index. Emits a downloadable .zip.

Pure standard library. Reads only SKILL.md text files (never binaries).

Usage:
    python3 export_skills.py [--out DIR] [--zip PATH] [--src PATH ...]
                             [--index-only] [--no-bodies-in-agents]

Discovery (auto, when no --src given), first existing of each is scanned:
    ~/.claude/skills/synced          (personal skills — one folder each)
    ~/.claude/skills                  (personal skills, alt layout)
    ~/.claude/plugins/synced/*/skills (plugin skills)
    ~/.claude/plugins/*/skills        (plugin skills, alt layout)
    ./.claude/skills                  (project-local)
    ./skills                          (project-local)
    $CLAUDE_SKILLS_PATH (colon-separated extra roots)

A "skill" is any directory containing a SKILL.md with YAML frontmatter that
has at least a `name`. Dedup is by skill name; personal skills win over plugin
skills, earlier sources win over later. Duplicates are recorded in the manifest.
"""

import argparse
import csv
import glob
import io
import os
import re
import sys
import zipfile
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def parse_frontmatter(text):
    """Return (frontmatter_dict, body_str). Uses PyYAML if available, else a
    minimal parser that handles name/description (quoted, folded, or plain)."""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm_text, body = m.group(1), m.group(2)
    try:
        import yaml  # optional
        data = yaml.safe_load(fm_text)
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items()}, body
    except Exception:
        pass
    # Minimal fallback: top-level "key: value" lines, values may fold onto
    # following indented lines.
    data = {}
    key = None
    buf = []
    for line in fm_text.splitlines():
        mk = re.match(r"^([A-Za-z0-9_-]+):\s?(.*)$", line)
        if mk and not line.startswith(" "):
            if key is not None:
                data[key] = " ".join(buf).strip()
            key = mk.group(1)
            buf = [mk.group(2)]
        elif key is not None:
            buf.append(line.strip())
    if key is not None:
        data[key] = " ".join(buf).strip()
    for k, v in list(data.items()):
        if isinstance(v, str):
            data[k] = v.strip().strip('"').strip("'").strip()
    return data, body


def default_sources():
    home = Path.home()
    cwd = Path.cwd()
    roots = []

    def add_direct(p):
        # A directory that directly contains <skill>/SKILL.md folders.
        roots.append(("dir", Path(p)))

    def add_glob(pat):
        for p in sorted(glob.glob(str(pat))):
            roots.append(("dir", Path(p)))

    add_direct(home / ".claude" / "skills" / "synced")
    add_direct(home / ".claude" / "skills")
    add_glob(home / ".claude" / "plugins" / "synced" / "*" / "skills")
    add_glob(home / ".claude" / "plugins" / "*" / "skills")
    add_direct(cwd / ".claude" / "skills")
    add_direct(cwd / "skills")
    for extra in os.environ.get("CLAUDE_SKILLS_PATH", "").split(os.pathsep):
        if extra.strip():
            add_direct(extra.strip())

    # Keep only existing, de-duplicated by resolved path.
    seen = set()
    out = []
    for kind, p in roots:
        if not p.exists() or not p.is_dir():
            continue
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        out.append(p)
    return out


def origin_for(skill_dir, root):
    """Human-readable origin tag for a skill folder."""
    root = Path(root)
    parts = root.parts
    if "plugins" in parts:
        # .../plugins/synced/<plugin>/skills  ->  plugin:<plugin>
        i = parts.index("plugins")
        # plugin name is the segment right before "skills"
        try:
            plugin = root.parts[list(root.parts).index("skills") - 1]
        except ValueError:
            plugin = root.name
        return f"plugin:{plugin}"
    return "personal"


def discover(sources):
    """Return (skills, duplicates). skills: list of dicts name/description/
    origin/body/path. duplicates: list of dicts for shadowed skills."""
    skills = {}
    duplicates = []
    errors = []
    # personal roots first so they win dedup
    ordered = sorted(sources, key=lambda p: 0 if "plugins" not in p.parts else 1)
    for root in ordered:
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            sm = entry / "SKILL.md"
            if not sm.exists():
                continue
            try:
                text = sm.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                errors.append((str(sm), str(e)))
                continue
            fm, body = parse_frontmatter(text)
            name = str(fm.get("name", "")).strip()
            desc = str(fm.get("description", "")).strip()
            origin = origin_for(entry, root)
            if not name:
                # fall back to folder name
                name = entry.name
            rec = {
                "name": name,
                "description": desc,
                "origin": origin,
                "body": body.strip(),
                "path": str(sm),
                "valid_name": bool(NAME_RE.match(name)),
            }
            if name in skills:
                duplicates.append({**rec, "shadowed_by": skills[name]["origin"]})
            else:
                skills[name] = rec
    return list(skills.values()), duplicates, errors


def slugify(name):
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "skill"


def emit(skills, duplicates, errors, out_dir, index_only, bodies_in_agents):
    out = Path(out_dir)
    (out / "skills").mkdir(parents=True, exist_ok=True)
    skills_sorted = sorted(skills, key=lambda s: s["name"].lower())

    # 1) Per-skill Claude / skills.sh layout: skills/<name>/SKILL.md
    used = set()
    for s in skills_sorted:
        slug = slugify(s["name"])
        base = slug
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        s["_slug"] = slug
        d = out / "skills" / slug
        d.mkdir(parents=True, exist_ok=True)
        fm_name = s["name"] if s["valid_name"] else slug
        content = (
            "---\n"
            f"name: {fm_name}\n"
            f"description: {escape_yaml(s['description'])}\n"
            f"metadata:\n"
            f"  origin: {s['origin']}\n"
            "---\n\n"
            + (s["body"] or f"# {s['name']}\n")
            + "\n"
        )
        (d / "SKILL.md").write_text(content, encoding="utf-8")

    # 2) The ONE combined skills.md master index
    lines = [
        "# Combined Skills Index (skills.md)",
        "",
        f"{len(skills_sorted)} skills discovered and combined from this agent's "
        "environment. Generated by skills-exporter.",
        "",
        "Each entry below is one skill: its name, origin, when-to-use "
        "description, and (unless index-only) its full instructions. Individual "
        "copies live under `skills/<name>/SKILL.md`; a Codex-compatible "
        "`AGENTS.md` and a `v0/` folder accompany this file.",
        "",
        "## Catalog",
        "",
        "| Skill | Origin | Description |",
        "| --- | --- | --- |",
    ]
    for s in skills_sorted:
        desc = s["description"].replace("|", "\\|").replace("\n", " ")
        if len(desc) > 200:
            desc = desc[:197] + "..."
        lines.append(f"| `{s['name']}` | {s['origin']} | {desc} |")
    lines.append("")
    if not index_only:
        lines.append("## Skills")
        lines.append("")
        for s in skills_sorted:
            lines.append(f"### {s['name']}")
            lines.append("")
            lines.append(f"- Origin: {s['origin']}")
            lines.append(f"- Source folder: `skills/{s['_slug']}/SKILL.md`")
            lines.append("")
            if s["description"]:
                lines.append(f"**When to use:** {s['description']}")
                lines.append("")
            lines.append(s["body"] or "_(no additional instructions)_")
            lines.append("")
            lines.append("---")
            lines.append("")
    (out / "skills.md").write_text("\n".join(lines), encoding="utf-8")

    # 3) Codex-compatible AGENTS.md
    a = [
        "# AGENTS.md — Combined Agent Skills",
        "",
        "This bundle packages skills discovered from an AI agent's environment "
        "so any agent that reads `AGENTS.md` (OpenAI Codex and compatible) can "
        "use them. Treat each skill below as an available capability: when a "
        "user's request matches a skill's *When to use* line, follow that "
        "skill's instructions.",
        "",
        "Full individual copies are under `skills/<name>/SKILL.md`. The same "
        "content in a single file is in `skills.md`.",
        "",
        f"**{len(skills_sorted)} skills available.**",
        "",
        "## Skill catalog",
        "",
    ]
    for s in skills_sorted:
        desc = s["description"] or "(no description)"
        a.append(f"- **{s['name']}** ({s['origin']}) — {desc} "
                 f"→ `skills/{s['_slug']}/SKILL.md`")
    a.append("")
    if bodies_in_agents and not index_only:
        a.append("## Skill instructions")
        a.append("")
        for s in skills_sorted:
            a.append(f"### {s['name']}")
            a.append("")
            if s["description"]:
                a.append(f"**When to use:** {s['description']}")
                a.append("")
            a.append(s["body"] or "_(no additional instructions)_")
            a.append("")
    (out / "AGENTS.md").write_text("\n".join(a), encoding="utf-8")

    # 4) v0.app-ready folder: v0 uses only name + description.
    (out / "v0").mkdir(exist_ok=True)
    v = [
        "# v0.app skills",
        "",
        "v0.app attaches skills to prompts using their `name` + `description` "
        "only (it has no shell/filesystem beyond the generated project). Every "
        "skill in this bundle is listed below; attach the ones relevant to a "
        "prompt. Instruction-only skills work as-is; skills that depend on "
        "shell/MCP/tools will not execute on v0 but their guidance still helps.",
        "",
        "| Skill | Description |",
        "| --- | --- |",
    ]
    for s in skills_sorted:
        desc = s["description"].replace("|", "\\|").replace("\n", " ")
        v.append(f"| `{s['name']}` | {desc} |")
    (out / "v0" / "skills-list.md").write_text("\n".join(v), encoding="utf-8")

    # 5) manifest.csv
    with open(out / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "slug", "origin", "status", "valid_name",
                    "source_path", "description"])
        for s in skills_sorted:
            w.writerow([s["name"], s["_slug"], s["origin"], "included",
                        s["valid_name"], s["path"],
                        s["description"].replace("\n", " ")])
        for d in duplicates:
            w.writerow([d["name"], slugify(d["name"]), d["origin"],
                        f"duplicate_shadowed_by:{d['shadowed_by']}",
                        d["valid_name"], d["path"],
                        d["description"].replace("\n", " ")])

    # 6) README
    r = [
        "# Combined Skills Export",
        "",
        f"- **{len(skills_sorted)} skills** combined from this agent's "
        "environment.",
        f"- **{len(duplicates)} duplicate** name(s) shadowed (see "
        "`manifest.csv`).",
        "",
        "## What's inside",
        "",
        "- `skills.md` — the single combined index of every skill (catalog + "
        "full instructions).",
        "- `AGENTS.md` — Codex-compatible entry point; same skills framed as "
        "agent instructions.",
        "- `skills/<name>/SKILL.md` — individual skills in Claude / skills.sh "
        "layout.",
        "- `v0/skills-list.md` — name+description list for attaching skills in "
        "v0.app.",
        "- `manifest.csv` — origin, slug, and dedup status for every skill.",
        "",
        "## Regenerate",
        "",
        "```bash",
        "python3 scripts/export_skills.py --out ./out --zip ./skills-export.zip",
        "```",
        "",
        "Bodies of duplicate/shadowed skills are omitted; the first occurrence "
        "wins (personal skills over plugin skills).",
    ]
    if errors:
        r.append("")
        r.append(f"> Note: {len(errors)} SKILL.md file(s) could not be read.")
    (out / "README.md").write_text("\n".join(r), encoding="utf-8")

    return skills_sorted


def escape_yaml(value):
    """Make a description safe as a single-line YAML scalar."""
    v = " ".join(str(value).split())
    if v and (v[0] in "!&*[]{}#|>@`\"'%,:" or ": " in v or v.endswith(":")):
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return v


def make_zip(out_dir, zip_path):
    out = Path(out_dir)
    zp = Path(zip_path)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(out.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(out))
    return zp


def main(argv=None):
    ap = argparse.ArgumentParser(description="Combine agent-accessible skills "
                                             "into a portable multi-agent zip.")
    ap.add_argument("--out", default="skills-export", help="output directory")
    ap.add_argument("--zip", default="skills-export.zip", help="output zip path")
    ap.add_argument("--src", action="append", default=[],
                    help="extra source root (repeatable); directory containing "
                         "<skill>/SKILL.md folders")
    ap.add_argument("--index-only", action="store_true",
                    help="skills.md/AGENTS.md list descriptions only, no bodies")
    ap.add_argument("--inline-agents", action="store_true",
                    help="inline full skill bodies into AGENTS.md too. Default "
                         "is a catalog + pointers, which keeps AGENTS.md small "
                         "enough for Codex to load (bodies live in "
                         "skills/<name>/SKILL.md and skills.md).")
    ap.add_argument("--no-zip", action="store_true", help="skip zipping")
    args = ap.parse_args(argv)

    sources = [Path(s) for s in args.src] if args.src else default_sources()
    sources = [s for s in sources if s.exists() and s.is_dir()]
    if not sources:
        print("No skill sources found. Pass --src <dir> pointing at a folder "
              "of <skill>/SKILL.md directories.", file=sys.stderr)
        return 2

    print(f"Scanning {len(sources)} source root(s):", file=sys.stderr)
    for s in sources:
        print(f"  - {s}", file=sys.stderr)

    skills, duplicates, errors = discover(sources)
    if not skills:
        print("No skills (SKILL.md files) found under the given sources.",
              file=sys.stderr)
        return 3

    emitted = emit(skills, duplicates, errors, args.out, args.index_only,
                   args.inline_agents)
    print(f"Combined {len(emitted)} skills ({len(duplicates)} duplicates "
          f"shadowed) into {args.out}/", file=sys.stderr)

    if not args.no_zip:
        zp = make_zip(args.out, args.zip)
        size = zp.stat().st_size
        print(f"Wrote {zp} ({size/1024:.0f} KB)", file=sys.stderr)
        print(str(zp))  # stdout: the deliverable path
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
