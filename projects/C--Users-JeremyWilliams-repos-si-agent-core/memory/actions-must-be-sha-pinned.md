---
name: actions-must-be-sha-pinned
description: si-agent-core enforces 40-char SHA pinning for every GitHub Actions `uses:` — including reusable workflows — so tag refs like @v1 fail CI.
metadata:
  type: project
---

`tests/unit/docs/test_documentation.py::test_actions_are_pinned_and_untrusted_ci_has_read_only_permissions`
asserts every `uses:` in `.github/**/*.yml` matches `@[0-9a-f]{40}$`. It applies to reusable
workflow calls too, not just actions, and it also pins the workflow count at 5.

Consequence: a caller like `org/repo/.github/workflows/x.yml@v1` fails CI. Pin the commit SHA
with the tag name as a trailing comment (`@<sha> # v1`) — the test's regex `uses:\s+([^\s#]+)`
stops at `#`, so the comment is safe.

The rule is deliberate and correct: a moving tag is a mutable reference, so whoever can move it
can repoint this repo's CI. Do not relax the test to accommodate a tag.

Trap when resolving a tag to a SHA: `git ls-remote <repo> v1` returns the **annotated tag
object's** hash, which is 40 hex chars and passes the format check but is not a commit and will
not resolve at run time. Use `git ls-remote <repo> 'v1^{}'` to dereference to the commit.

Established 2026-09-24 while wiring `Dobeu-tech-eco/standards` as a shared CI baseline.
Related: [[windows-uv-venv-lib64-repair]]
