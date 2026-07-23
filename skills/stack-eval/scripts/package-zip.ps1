#Requires -Version 5.1
<#
.SYNOPSIS
  Build dist/stack-eval.zip for claude.ai / Cowork Skills upload.

  Archive layout (required by Claude Skills packaging):
    stack-eval.zip
    └── stack-eval/
        ├── SKILL.md
        ├── INSTALL.md
        ├── references/
        └── scripts/
#>
param(
  [string]$SotRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $SotRoot) {
  $SotRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$skillName = "stack-eval"
$skillMd = Join-Path $SotRoot "SKILL.md"
if (-not (Test-Path -LiteralPath $skillMd)) {
  throw "SoT missing SKILL.md at $SotRoot"
}

$distDir = Join-Path $SotRoot "dist"
$zipPath = Join-Path $distDir "$skillName.zip"
$stageRoot = Join-Path $env:TEMP ("stack-eval-zip-" + [guid]::NewGuid().ToString("N"))
$stageSkill = Join-Path $stageRoot $skillName

try {
  New-Item -ItemType Directory -Force -Path $stageSkill | Out-Null

  $include = @("SKILL.md", "INSTALL.md", "references", "scripts")
  foreach ($name in $include) {
    $src = Join-Path $SotRoot $name
    if (-not (Test-Path -LiteralPath $src)) { continue }
    $dest = Join-Path $stageSkill $name
    Copy-Item -LiteralPath $src -Destination $dest -Recurse -Force
  }

  if (-not (Test-Path -LiteralPath $distDir)) {
    New-Item -ItemType Directory -Force -Path $distDir | Out-Null
  }
  if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
  }

  Compress-Archive -Path $stageSkill -DestinationPath $zipPath -CompressionLevel Optimal
  Write-Host "Wrote $zipPath"
}
finally {
  if (Test-Path -LiteralPath $stageRoot) {
    Remove-Item -LiteralPath $stageRoot -Recurse -Force
  }
}
