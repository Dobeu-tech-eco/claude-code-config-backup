#Requires -Version 5.1
<#
.SYNOPSIS
  Sync stack-eval skill from SoT to local install paths.

.PARAMETER IncludeRepoCursor
  Also mirror to <repo>/.cursor/skills/stack-eval

.PARAMETER SotRoot
  Override SoT directory (defaults to parent of scripts/)
#>
param(
  [switch]$IncludeRepoCursor,
  [string]$SotRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $SotRoot) {
  $SotRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$skillName = "stack-eval"
if (-not (Test-Path (Join-Path $SotRoot "SKILL.md"))) {
  throw "SoT missing SKILL.md at $SotRoot"
}

$userProfile = $env:USERPROFILE
if (-not $userProfile) { throw "USERPROFILE not set" }

# Detect repo root (parent of .claude)
$repoRoot = $null
$cursor = Get-Item $SotRoot
while ($cursor -ne $null) {
  if ((Split-Path $cursor.FullName -Leaf) -eq ".claude") {
    $repoRoot = $cursor.Parent.FullName
    break
  }
  $cursor = $cursor.Parent
}

$destinations = @(
  (Join-Path $userProfile ".cursor\skills\$skillName"),
  (Join-Path $userProfile ".claude\skills\$skillName"),
  (Join-Path $userProfile ".codex\skills\$skillName"),
  (Join-Path $userProfile ".agents\skills\$skillName")
)

if ($IncludeRepoCursor) {
  if (-not $repoRoot) { throw "Could not resolve repo root for .cursor/skills mirror" }
  $destinations += (Join-Path $repoRoot ".cursor\skills\$skillName")
}

function Copy-SkillMirror {
  param([string]$Source, [string]$Dest)
  if (Test-Path $Dest) {
    Remove-Item -LiteralPath $Dest -Recurse -Force
  }
  $parent = Split-Path $Dest -Parent
  if (-not (Test-Path $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  Copy-Item -LiteralPath $Source -Destination $Dest -Recurse -Force
  Write-Host "Synced -> $Dest"
}

Write-Host "SoT: $SotRoot"
foreach ($dest in $destinations) {
  Copy-SkillMirror -Source $SotRoot -Dest $dest
}

Write-Host ""
Write-Host "Local sync complete. Manual uploads still required for:"
Write-Host "  - claude.ai Skills (zip upload)"
Write-Host "  - Claude Cowork Skills UI"
Write-Host "  - ChatGPT Codex online skill install"
Write-Host "Optional backup: G:\My Drive\claude\skills\$skillName (see INSTALL.md)"
