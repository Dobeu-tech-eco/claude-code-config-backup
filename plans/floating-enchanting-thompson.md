# Plan: Preserve local `main` as `main-msi`, PR it, and re-sync local `main` to remote

## Context

The local `main` branch has **diverged** from `origin/main` (the GitKraken worktree warning in the
screenshot). Concretely:

- Local `main` = `8febbc9`, tracking `origin/main`, **ahead 1 / behind 2**.
- The 1 local-only commit: `8febbc9 chore: add full autonomous loop protocol for Vercel full-stack coding agent`.
- `origin/main` = `e2d43e5`, which has 2 commits local `main` lacks: `e2d43e5` (#182) and `ef649e4` (#181).
- Merge base: `7ce3872`.

The user wants the remote to be the source of truth: rescue the one local commit onto a new branch
`main-msi`, push it and open a PR against `origin/main`, then reset local `main` to exactly match
`origin/main` so the divergence warning clears and new worktrees created from `origin/main` no longer
exclude local commits.

Verified prerequisites:
- `main` is **not checked out** in any worktree (main repo is on `feature/hardening-audit-and-landing-refresh`;
  this worktree is on `main-to-remote`), so it can be renamed/recreated safely without a checkout.
- `origin/main-msi` does **not** yet exist remotely — the push creates it cleanly.
- `gh` 2.96.0 is authed as `dobeutech` on `github.com/dobeu-tech-eco/new-dobeu-net`.
- No data is lost: commit `8febbc9` is preserved on `main-msi` before `main` is moved.

## Steps (run from `c:/Users/JeremyWilliams/repos/new-dobeu-net`)

1. **Refresh remote truth**
   `git fetch origin --prune`

2. **Rename local `main` → `main-msi`** (carries the local commit `8febbc9`)
   `git branch -m main main-msi`

3. **Recreate local `main` at the remote tip, tracking it** (this clears the divergence)
   `git branch --track main origin/main`
   Result: local `main` = `e2d43e5`, identical to `origin/main`, ahead 0 / behind 0.

4. **Push `main-msi` to remote and set upstream** (no checkout needed)
   `git push -u origin main-msi`
   Creates `origin/main-msi` and repoints `main-msi`'s upstream to it.

5. **Open the PR against remote `main`**
   `gh pr create --base main --head main-msi --title "chore: autonomous loop protocol for Vercel full-stack coding agent" --body "<summary of the 8febbc9 change; PR to land the local-only main commit onto origin/main>"`

## Notes / decisions

- Using `git branch --track main origin/main` (not a hard reset of a checked-out branch) because `main`
  is unchecked-out; this is the least-risk way to make local `main` == `origin/main`.
- The two `.Jules/*.md` untracked files in the current worktree are unrelated scratch notes and are left
  untouched (per CLAUDE.md "untracked working-tree noise").
- No `Co-Authored-By` trailer is added (per repo CLAUDE.md; no commits are authored here anyway — only a
  branch rename + push of an existing commit).

## Verification

After execution, confirm:
- `git branch -vv` shows `main  e2d43e5 [origin/main]` with **no** "ahead/behind" (divergence cleared),
  and `main-msi  8febbc9 [origin/main-msi]`.
- `git log --oneline origin/main..main` is empty; `git log --oneline main..origin/main` is empty.
- `git ls-remote --heads origin main-msi` returns the new remote branch.
- `gh pr view main-msi` shows an open PR into `main` containing exactly commit `8febbc9`.
- Re-opening the "new worktree from origin/main" dialog no longer shows the "local main has diverged"
  warning.
