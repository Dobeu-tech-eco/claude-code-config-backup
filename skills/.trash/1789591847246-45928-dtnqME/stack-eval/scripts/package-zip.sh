#!/usr/bin/env bash
# Build dist/stack-eval.zip for claude.ai / Cowork Skills upload.
# Layout: stack-eval.zip → stack-eval/SKILL.md (folder as zip root entry).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOT_ROOT="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"
SKILL_NAME="stack-eval"

if [[ ! -f "$SOT_ROOT/SKILL.md" ]]; then
  echo "SoT missing SKILL.md at $SOT_ROOT" >&2
  exit 1
fi

DIST_DIR="$SOT_ROOT/dist"
ZIP_PATH="$DIST_DIR/$SKILL_NAME.zip"
STAGE_ROOT="$(mktemp -d)"
STAGE_SKILL="$STAGE_ROOT/$SKILL_NAME"

cleanup() { rm -rf "$STAGE_ROOT"; }
trap cleanup EXIT

mkdir -p "$STAGE_SKILL" "$DIST_DIR"
for name in SKILL.md INSTALL.md references scripts; do
  if [[ -e "$SOT_ROOT/$name" ]]; then
    cp -R "$SOT_ROOT/$name" "$STAGE_SKILL/"
  fi
done

rm -f "$ZIP_PATH"
# -X omit extra attrs; -r recurse; run from stage so zip contains stack-eval/...
( cd "$STAGE_ROOT" && zip -r -X "$ZIP_PATH" "$SKILL_NAME" )
echo "Wrote $ZIP_PATH"
