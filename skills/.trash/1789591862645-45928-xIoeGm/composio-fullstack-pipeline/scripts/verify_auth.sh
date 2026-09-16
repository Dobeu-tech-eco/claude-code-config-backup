#!/usr/bin/env bash
# verify_auth.sh — Pre-flight check for Claude Code Max-subscription auth.
#
# Confirms:
#   1. ANTHROPIC_API_KEY is unset (else it overrides the OAuth credential).
#   2. The Claude Code credential file exists.
#
# Run from inside Claude Code's environment, NOT from a CI runner.
# CI should use ANTHROPIC_API_KEY (the paid API surface) — Max-sub OAuth
# is licensed for Claude Code & Claude.ai only per the April 2026 TOS.

set -u

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }

echo "Claude Code auth pre-flight"
echo "---------------------------"

# 1. ANTHROPIC_API_KEY check
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  red "FAIL: ANTHROPIC_API_KEY is set."
  echo "      The API key takes precedence over the /login OAuth credential."
  echo "      Fix: 'unset ANTHROPIC_API_KEY' in your shell, remove from rc files,"
  echo "      then restart Claude Code."
  AUTH_OK=0
else
  green "OK:   ANTHROPIC_API_KEY is unset."
  AUTH_OK=1
fi

# 2. Credential file check (best-effort across platforms)
CRED_FOUND=0
for path in \
  "${HOME}/.config/claude/credentials.json" \
  "${HOME}/Library/Application Support/Claude/credentials.json" \
  "${APPDATA:-$HOME/AppData/Roaming}/Claude/credentials.json"
do
  if [[ -f "$path" ]]; then
    green "OK:   Credential file present at: $path"
    CRED_FOUND=1
    break
  fi
done

if [[ $CRED_FOUND -eq 0 ]]; then
  yellow "WARN: No credential file found in known locations."
  echo "      If you haven't run /login yet, do so now inside Claude Code."
  echo "      If you have, the credential location may have moved — check"
  echo "      https://code.claude.com/docs/en/authentication"
fi

# 3. Recommend /status
echo ""
echo "Next: inside Claude Code, run /status and confirm:"
echo "      Authentication: Subscription (Max)"
echo ""

# Exit code
if [[ $AUTH_OK -eq 1 && $CRED_FOUND -eq 1 ]]; then
  green "Pre-flight green. Proceed."
  exit 0
else
  red "Pre-flight failed. Resolve issues above before proceeding."
  exit 1
fi
