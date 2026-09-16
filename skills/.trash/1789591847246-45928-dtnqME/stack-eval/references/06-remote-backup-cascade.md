# P6 — Remote backup cascade

## Goal

Ensure primary remote works, then offer ordered backup remotes. Never commit secrets.

## Exact cascade order

1. **GitHub** — verify `origin` fetch/push (this monorepo often already has GitHub; verify first).
2. **GitLab** — offer as backup remote if user has access.
3. **Bitbucket** — next.
4. **DockerHub** — only if container publish is in end-state.
5. **npmjs** — only if package publish is in end-state.
6. **Other** — ask the user.

## Steps

1. Inspect remotes (`git remote -v`).
2. Verify GitHub push capability (dry or status). If already present → confirm, then continue cascade for **backup** remotes only.
3. For each next target: prompt for access. If declined → fall through to next. Never block the pipeline on decline.
4. Record results in `.agent/remotes.md` (accepted / declined / skipped / failed + reason).
5. Never store tokens in git. Never force-add remotes without user consent.

## STOP / CONTINUE

- **STOP:** Only if primary remote is broken **and** user has not acknowledged proceeding without push (see P13).
- **CONTINUE:** Cascade completed (declines are success paths).

## Outputs

- `.agent/remotes.md`
