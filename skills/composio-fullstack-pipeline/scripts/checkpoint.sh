#!/usr/bin/env bash
# checkpoint.sh — Refresh .agent/state.json from the current git + build state.
#
# Run from the repo root. Designed to be cheap (≤2s) so you can run it often.
# Does NOT commit; the caller decides when to commit.

set -eu

if [[ ! -d ".agent" ]]; then
  echo "ERROR: .agent/ directory not found. Run scripts/bootstrap_session.sh first."
  exit 1
fi

CHECKPOINT_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
HEAD_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo 'no-commits')"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'detached')"
DIRTY=$(if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then echo "true"; else echo "false"; fi)

# Build / test status — best-effort, ignoring tools not present
LINT="not_run"
TYPECHECK="not_run"
BUILD="not_run"
TESTS="not_run"

if command -v npm >/dev/null 2>&1 && [[ -f package.json ]]; then
  if npm run --silent lint >/dev/null 2>&1; then LINT="pass"; else LINT="fail"; fi
  if npm run --silent typecheck >/dev/null 2>&1; then TYPECHECK="pass"; else TYPECHECK="fail"; fi
fi

# Write state.json
cat > .agent/state.json <<JSON
{
  "session": {
    "checkpointed_at": "${CHECKPOINT_AT}"
  },
  "repo": {
    "branch": "${BRANCH}",
    "head_sha": "${HEAD_SHA}",
    "uncommitted_changes": ${DIRTY}
  },
  "build": {
    "lint": "${LINT}",
    "typecheck": "${TYPECHECK}",
    "build": "${BUILD}",
    "tests": "${TESTS}"
  },
  "_note": "This file is overwritten by checkpoint.sh on each run. Hand-edit after the script if you need to add fields like deploy URL or connection health."
}
JSON

echo "Checkpoint written to .agent/state.json"
echo "  branch:  ${BRANCH}"
echo "  HEAD:    ${HEAD_SHA}"
echo "  dirty:   ${DIRTY}"
echo "  lint:    ${LINT}"
echo "  type:    ${TYPECHECK}"
echo ""
echo "Don't forget to:"
echo "  1. Append a one-liner to .agent/progress.md describing this checkpoint."
echo "  2. Commit if there are uncommitted changes."
