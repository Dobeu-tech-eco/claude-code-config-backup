---
name: ntn-dts-work-lives-in-wsl
description: The ntn-dts-work Notion Workers project lives in WSL ext4 at ~/ntn-dts-work, deliberately not under repos\
metadata:
  type: project
---

`ntn-dts-work` is a Notion Workers project (`@notion-cookbook/workers-default`
scaffold: `@notionhq/workers`, `.agents/skills/`, `src/index.ts`). It is driven
from **WSL**, and lives at WSL ext4 `/home/jeremyw/ntn-dts-work` — NOT under
`C:\Users\JeremyWilliams\repos\`.

Decision (2026-09-15, owner): moved out of `repos\` on purpose, because that tree
is Google-Drive-synced and `/mnt/c` is slow 9p — see
[[repos-is-google-drive-synced]]. Do not "helpfully" move it back under `repos\`.

Origin: `ntn workers init` took the project name `login`, so it originally
scaffolded to `~\login` with a stray `git init` (0 commits, no remote). Install
deps with `npm ci` inside WSL (~5s on ext4); `npm run check` must exit 0.
A Windows-side `npm install` would produce an unusable tree — see
[[notion-cli-windows-npm-only]].
