#!/usr/bin/env bash
# Sync stack-eval skill from SoT to local install paths.
set -euo pipefail

INCLUDE_REPO_CURSOR=0
SOT_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --include-repo-cursor) INCLUDE_REPO_CURSOR=1; shift ;;
    --sot) SOT_ROOT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "$SOT_ROOT" ]]; then
  SOT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

SKILL_NAME="stack-eval"
if [[ ! -f "$SOT_ROOT/SKILL.md" ]]; then
  echo "SoT missing SKILL.md at $SOT_ROOT" >&2
  exit 1
fi

HOME_DIR="${HOME:-}"
if [[ -z "$HOME_DIR" ]]; then
  echo "HOME not set" >&2
  exit 1
fi

# Resolve repo root (parent of .claude)
REPO_ROOT=""
cur="$SOT_ROOT"
while [[ "$cur" != "/" ]]; do
  base="$(basename "$cur")"
  if [[ "$base" == ".claude" ]]; then
    REPO_ROOT="$(dirname "$cur")"
    break
  fi
  cur="$(dirname "$cur")"
done

DESTS=(
  "$HOME_DIR/.cursor/skills/$SKILL_NAME"
  "$HOME_DIR/.claude/skills/$SKILL_NAME"
  "$HOME_DIR/.codex/skills/$SKILL_NAME"
  "$HOME_DIR/.agents/skills/$SKILL_NAME"
)

if [[ "$INCLUDE_REPO_CURSOR" -eq 1 ]]; then
  if [[ -z "$REPO_ROOT" ]]; then
    echo "Could not resolve repo root for .cursor/skills mirror" >&2
    exit 1
  fi
  DESTS+=("$REPO_ROOT/.cursor/skills/$SKILL_NAME")
fi

mirror() {
  local src="$1" dest="$2"
  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  cp -R "$src" "$dest"
  echo "Synced -> $dest"
}

echo "SoT: $SOT_ROOT"
for dest in "${DESTS[@]}"; do
  mirror "$SOT_ROOT" "$dest"
done

echo ""
echo "Local sync complete. Manual uploads still required for:"
echo "  - claude.ai Skills (zip upload)"
echo "  - Claude Cowork Skills UI"
echo "  - ChatGPT Codex online skill install"
echo "Optional backup: G:\\My Drive\\claude\\skills\\$SKILL_NAME (see INSTALL.md)"
