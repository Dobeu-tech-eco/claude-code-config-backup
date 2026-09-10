#!/usr/bin/env node
/*
 * Cross-platform launcher for the Windows-side hooks in this directory.
 *
 * Why this exists
 * ---------------
 * C:\Users\JeremyWilliams\.claude\settings.json is the WINDOWS global config, but a WSL
 * session started anywhere under that tree also loads it as PROJECT settings. Its hook
 * commands used Windows interpreters and Windows-drive paths, so under WSL every Bash
 * tool call produced:
 *
 *     pwsh: command not found                                  (exit 127)
 *     Error: Cannot find module '/home/<user>/C:/Users/.../x.js'
 *
 * Naively repointing those commands at portable paths would make them RUN under WSL --
 * but the WSL config at ~/.claude/settings.json already runs the Linux equivalents of
 * these same hooks, so they would fire twice per event.
 *
 * So: on Windows, run the requested script exactly as before. On any other platform,
 * exit 0 silently and let the WSL user-scope config own it.
 *
 * Usage (from settings.json):
 *     node "${CLAUDE_PROJECT_DIR}/.claude/hooks/win-only-hook.js" <script-relative-to-this-dir>
 *
 * Exit codes are propagated verbatim -- this matters: PreToolUse blocks on exit 2 and
 * ONLY exit 2, so a secret-scan hit must not be flattened to 0 or 1 on the way out.
 */

'use strict';

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Fail open: a broken launcher must never wedge the user's tool calls.
function bail() { process.exit(0); }

const rel = process.argv[2];
if (!rel) bail();

// Anything but Windows: the WSL user-scope config already handles these hooks.
if (process.platform !== 'win32') bail();

const target = path.join(__dirname, rel);
if (!fs.existsSync(target)) bail();

// Hooks read their payload from stdin; forward it verbatim.
let input = '';
try {
  input = fs.readFileSync(0, 'utf8');
} catch {
  input = '';
}

function exec(cmd, args) {
  const res = spawnSync(cmd, args, {
    input,
    stdio: ['pipe', 'inherit', 'inherit'],
    windowsHide: true,
  });
  if (res.error) return null;
  return typeof res.status === 'number' ? res.status : 0;
}

let status = null;

if (target.toLowerCase().endsWith('.ps1')) {
  // Prefer PowerShell 7; fall back to Windows PowerShell 5.1.
  for (const exe of ['pwsh', 'powershell']) {
    status = exec(exe, ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', target]);
    if (status !== null) break;
  }
} else {
  status = exec(process.execPath, [target]);
}

process.exit(status === null ? 0 : status);
