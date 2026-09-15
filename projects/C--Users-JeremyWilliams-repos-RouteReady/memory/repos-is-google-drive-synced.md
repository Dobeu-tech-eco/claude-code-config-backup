---
name: repos-is-google-drive-synced
description: C:\Users\JeremyWilliams\repos is mirrored by Google Drive for Desktop, which has no per-folder ignore — node_modules uploads
metadata:
  type: reference
---

`C:\Users\JeremyWilliams\repos` is an actively synced Google Drive for Desktop
folder (`GoogleDriveFS` process; `.tmp.driveupload` / `.tmp.drivedownload` sit in
the repos root and stage thousands of files).

**Google Drive for Desktop has no ignore-file mechanism** — it cannot be told to
skip `node_modules`, and it does not read `.gitignore`. So any Node project placed
under `repos\` uploads its whole dependency tree to Drive and re-uploads on every
install. Confirmed 2026-09-14: one scaffold contributed 1,357 node_modules files
(70 MB) to a 3,893-item upload queue.

Implication: for a WSL-driven Node project, prefer WSL ext4 (`~/project`) over
`repos\`. That also avoids the slow `/mnt/c` 9p path. See
[[ntn-dts-work-lives-in-wsl]].
