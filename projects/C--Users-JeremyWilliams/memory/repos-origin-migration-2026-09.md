---
name: repos-origin-migration-2026-09
description: "On 2026-09-15, 57 of 61 repos were repointed to Cursor Origin; 4 were deliberately skipped and still need a decision."
metadata: 
  node_type: memory
  type: project
  originSessionId: 3e22f99a-b40f-4133-a03f-7f6bc702bfce
  modified: 2026-09-15T20:23:13.387Z
---

On **2026-09-15**, every mirrored repo under `C:\Users\JeremyWilliams\repos` had its local
`origin` remote repointed from GitHub to `https://origin.cursor.com/dobeutech/{repo}.git`.
The original GitHub URL was preserved on each repo as a **`github` remote**.

GitHub remains the source of truth — see [[cursor-origin-git-forge]]. This was deliberately a
mirror repoint, **not** a detach, so the 22 repos with GitHub Actions keep working.

**4 repos deliberately skipped, still needing a decision:**

- `ecc` — fork of `affaan-m/ECC`, third-party org; also carries a second `dobeu` remote
- `claude-devfleet` — `LEC-AI/claude-devfleet`, third-party org
- `dobeu-v0-skills-pack` — name-collides with `dobeutech_dobeu-v0-skills-pack`; the two come from
  *different* GitHub orgs but map to the same flat Origin URL
- `gcloudgenai` — a git repo with **no remotes at all**

Artifacts live in `.omc/state/origin-migration/`: `remotes-backup.tsv` (122 original entries),
`plan.tsv` (the 57-row map), and `rollback.sh` (full revert). Spec at
`.omc/specs/deep-interview-origin-migration.md`.

**Never verified:** that the Origin URLs actually resolve. The `origin` CLI was not installed and
no git credential helper was set, so no authenticated round-trip was ever tested.
