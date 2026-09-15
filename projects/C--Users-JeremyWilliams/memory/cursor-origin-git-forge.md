---
name: cursor-origin-git-forge
description: Cursor Origin is a git forge whose GitHub mirror is one-way; the dobeutech namespace is flat and permanent.
metadata: 
  node_type: memory
  type: project
  originSessionId: 3e22f99a-b40f-4133-a03f-7f6bc702bfce
  modified: 2026-09-15T20:23:00.872Z
---

Cursor Origin (origin.cursor.com) is Cursor's git forge. Pro/Teams/Enterprise only, early beta.

Semantics that are easy to get wrong:

- "Sync from GitHub" mirroring is **strictly one-way — GitHub stays the source of truth.**
  Pushing to `https://origin.cursor.com/{owner}/{repo}.git` on a mirrored repo **proxies the push
  to GitHub**; Origin updates after GitHub accepts. So repointing a local remote to Origin is
  low-risk and reversible, and GitHub Actions keep firing.
- Becoming genuinely Origin-hosted requires Settings > General > **Detach from GitHub**, or a
  native `origin repo create`.
- **Not mirrored:** GitHub Issues, Actions workflows, secrets. Git history, branches, tags and
  PRs are mirrored.
- Branches named `origin` / `origin/*` are reserved; `origin push local` targets a `/local`
  endpoint that exists only on mirrored repos.
- Remote URL format is always `https://origin.cursor.com/{owner}/{repo}.git`.

For this user (as of 2026-09-15): the Origin namespace is **`dobeutech`, flat** — every repo lands
at `origin.cursor.com/dobeutech/{repo}.git` regardless of its GitHub org (`dobeu-tech-eco`,
`Dobeu-tech-eco`, and `dobeutech` all collapse into it). The namespace is **permanent during
beta**. Because it is flat, two repos with the same name in different GitHub orgs collide.

See [[repos-origin-migration-2026-09]] for what was actually migrated.
