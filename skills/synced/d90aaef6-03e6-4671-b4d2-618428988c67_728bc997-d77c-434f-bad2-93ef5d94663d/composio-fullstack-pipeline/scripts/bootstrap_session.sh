#!/usr/bin/env bash
# bootstrap_session.sh — Scaffold .agent/ from the templates if not already present.
#
# Idempotent: safe to run on an existing project — won't clobber existing artifacts.
# Run from the repo root.

set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEMPLATE_DIR="${SKILL_DIR}/assets/pipeline-template"

if [[ ! -d "${TEMPLATE_DIR}" ]]; then
  echo "ERROR: pipeline template not found at ${TEMPLATE_DIR}"
  exit 1
fi

mkdir -p .agent

for f in tasks.json progress.md state.json handoff.md; do
  if [[ -f ".agent/$f" ]]; then
    echo "skip:  .agent/$f already exists"
  else
    cp "${TEMPLATE_DIR}/$f" ".agent/$f"
    echo "made:  .agent/$f"
  fi
done

# Substitute today's date and project name where templates use placeholders
TODAY="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PROJECT_NAME="$(basename "$(pwd)")"

# Use sed in a portable way (BSD sed on macOS doesn't support -i without arg)
sed_inplace() {
  if sed --version >/dev/null 2>&1; then
    sed -i "$@"     # GNU
  else
    sed -i '' "$@"  # BSD
  fi
}

for f in tasks.json state.json handoff.md; do
  if grep -q '__PROJECT_NAME__' ".agent/$f" 2>/dev/null; then
    sed_inplace "s/__PROJECT_NAME__/${PROJECT_NAME}/g" ".agent/$f"
  fi
  if grep -q '__TIMESTAMP__' ".agent/$f" 2>/dev/null; then
    sed_inplace "s/__TIMESTAMP__/${TODAY}/g" ".agent/$f"
  fi
done

echo ""
echo "Bootstrap complete. Next: catalog Composio connections and run the planner."
