#Requires -Version 7.0
<#
.SYNOPSIS
  Secret-safe CP0 backup of live AI-tool configuration surfaces.
#>
param(
  [string]$HubRoot = "C:\Users\JeremyWilliams\.claude\ai-stack-sync",
  [string]$DriveMirrorRoot = "G:\My Drive\claude\ai-stack-sync-backups"
)

$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupRoot = Join-Path $HubRoot "backups\CP0-$stamp"
$manifestPath = Join-Path $backupRoot "manifest.json"

$secretNamePattern = '(?i)(credential|auth\.json|token|secret|\.env$|\.env\.|cookies?|keychain|login)'
$inlineSecretPattern = '(?i)(sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z\-_]{20,}|Bearer\s+[A-Za-z0-9\-._~+/]+=*|X-API-Key["'':\s]+[A-Za-z0-9_\-]{16,})'

$candidates = @(
  @{ Rel = "claude-desktop\claude_desktop_config.json"; Path = "$env:APPDATA\Claude\claude_desktop_config.json" },
  @{ Rel = "claude-code\settings.json"; Path = "$env:USERPROFILE\.claude\settings.json" },
  @{ Rel = "claude-code\settings.local.json"; Path = "$env:USERPROFILE\.claude\settings.local.json" },
  @{ Rel = "claude-code\CLAUDE.md"; Path = "$env:USERPROFILE\.claude\CLAUDE.md" },
  @{ Rel = "claude-code\mcp-scaffold.json"; Path = "$env:USERPROFILE\.claude\mcp-scaffold.json" },
  @{ Rel = "claude-code\statusline.ps1"; Path = "$env:USERPROFILE\.claude\statusline.ps1" },
  @{ Rel = "home\CLAUDE.md"; Path = "$env:USERPROFILE\CLAUDE.md" },
  @{ Rel = "home\AGENTS.md"; Path = "$env:USERPROFILE\AGENTS.md" },
  @{ Rel = "codex\config.toml"; Path = "$env:USERPROFILE\.codex\config.toml" },
  @{ Rel = "codex\AGENTS.md"; Path = "$env:USERPROFILE\.codex\AGENTS.md" },
  @{ Rel = "codex\hooks.json"; Path = "$env:USERPROFILE\.codex\hooks.json" },
  @{ Rel = "cursor\mcp.json"; Path = "$env:USERPROFILE\.cursor\mcp.json" },
  @{ Rel = "cursor\cli-config.json"; Path = "$env:USERPROFILE\.cursor\cli-config.json" },
  @{ Rel = "cursor\User-settings.json"; Path = "$env:APPDATA\Cursor\User\settings.json" },
  @{ Rel = "agents\.skill-lock.json"; Path = "$env:USERPROFILE\.agents\.skill-lock.json" }
)

# Directory trees (config-only copies)
$dirCandidates = @(
  @{ Rel = "claude-code\rules"; Path = "$env:USERPROFILE\.claude\rules" },
  @{ Rel = "claude-code\hooks"; Path = "$env:USERPROFILE\.claude\hooks" },
  @{ Rel = "codex\rules"; Path = "$env:USERPROFILE\.codex\rules" },
  @{ Rel = "codex\hooks"; Path = "$env:USERPROFILE\.codex\hooks" }
)

New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$entries = @()
$skipped = @()

function Test-SafeContent {
  param([string]$Path)
  $name = Split-Path $Path -Leaf
  if ($name -match $secretNamePattern) { return $false }
  if ($Path -match '(?i)\\(auth\.json|credentials\.json|\.credentials\.json)$') { return $false }
  $ext = [IO.Path]::GetExtension($Path).ToLowerInvariant()
  if ($ext -notin @('.json', '.toml', '.md', '.ps1', '.js', '.yml', '.yaml', '.txt', '.rules')) {
    return $false
  }
  $raw = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
  if ($raw -match $inlineSecretPattern) { return $false }
  # Codex config may contain inline API keys - redact if present by skipping raw and writing sanitized note
  if ($Path -match '(?i)\\.codex\\config\.toml$' -and $raw -match '(?i)X-API-Key\s*=') {
    return 'sanitize-codex'
  }
  return $true
}

function Copy-SafeFile {
  param($Item)
  $src = $Item.Path
  $dest = Join-Path $backupRoot $Item.Rel
  if (-not (Test-Path -LiteralPath $src)) {
    $script:skipped += @{ Path = $src; Reason = "missing" }
    return
  }
  $safe = Test-SafeContent -Path $src
  if ($safe -eq $false) {
    $script:skipped += @{ Path = $src; Reason = "secret_or_unsafe" }
    return
  }
  $destDir = Split-Path $dest -Parent
  New-Item -ItemType Directory -Force -Path $destDir | Out-Null
  if ($safe -eq 'sanitize-codex') {
    $raw = Get-Content -LiteralPath $src -Raw
    # Redact header/API key values while preserving structure
    $sanitized = [regex]::Replace($raw, '(?im)(X-API-Key\s*=\s*")[^"]*(")', '$1***REDACTED***$2')
    $sanitized = [regex]::Replace($sanitized, '(?im)(api[_-]?key\s*=\s*")[^"]*(")', '$1***REDACTED***$2')
    Set-Content -LiteralPath $dest -Value $sanitized -Encoding utf8NoBOM
    $hash = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
    $script:entries += @{ Rel = $Item.Rel; Source = $src; Sha256 = $hash; Sanitized = $true }
  } else {
    Copy-Item -LiteralPath $src -Destination $dest -Force
    $hash = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
    $script:entries += @{ Rel = $Item.Rel; Source = $src; Sha256 = $hash; Sanitized = $false }
  }
}

foreach ($c in $candidates) { Copy-SafeFile -Item $c }

foreach ($d in $dirCandidates) {
  if (-not (Test-Path -LiteralPath $d.Path)) {
    $skipped += @{ Path = $d.Path; Reason = "missing" }
    continue
  }
  Get-ChildItem -LiteralPath $d.Path -Recurse -File | ForEach-Object {
    $relInside = $_.FullName.Substring($d.Path.Length).TrimStart('\','/')
    Copy-SafeFile -Item @{ Rel = (Join-Path $d.Rel $relInside); Path = $_.FullName }
  }
}

# Claude MCP server names only (no full .claude.json dump - contains OAuth/cache)
$claudeJson = "$env:USERPROFILE\.claude.json"
if (Test-Path $claudeJson) {
  try {
    $j = Get-Content -LiteralPath $claudeJson -Raw | ConvertFrom-Json -AsHashtable
    $mcpSummary = [ordered]@{
      capturedAt = (Get-Date).ToString("o")
      globalMcpServers = @($j.mcpServers.Keys)
      projectCount = @($j.projects.Keys).Count
      note = "Full .claude.json intentionally omitted from backup (secrets/session cache)."
    }
    $summaryPath = Join-Path $backupRoot "claude-code\claude-json-mcp-summary.json"
    New-Item -ItemType Directory -Force -Path (Split-Path $summaryPath -Parent) | Out-Null
    ($mcpSummary | ConvertTo-Json -Depth 5) | Set-Content -LiteralPath $summaryPath -Encoding utf8NoBOM
    $hash = (Get-FileHash -LiteralPath $summaryPath -Algorithm SHA256).Hash
    $entries += @{ Rel = "claude-code\claude-json-mcp-summary.json"; Source = $claudeJson; Sha256 = $hash; Sanitized = $true }
  } catch {
    $skipped += @{ Path = $claudeJson; Reason = "parse_failed:$($_.Exception.Message)" }
  }
}

$manifest = [ordered]@{
  id = "CP0-$stamp"
  createdAt = (Get-Date).ToString("o")
  backupRoot = $backupRoot
  entryCount = $entries.Count
  skippedCount = $skipped.Count
  entries = $entries
  skipped = $skipped
}
($manifest | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM

$driveOk = $false
$drivePath = $null
if (Test-Path "G:\My Drive") {
  $drivePath = Join-Path $DriveMirrorRoot "CP0-$stamp"
  New-Item -ItemType Directory -Force -Path $drivePath | Out-Null
  Copy-Item -LiteralPath $backupRoot -Destination $drivePath -Recurse -Force
  $driveOk = $true
}

$result = [ordered]@{
  ok = $true
  id = "CP0-$stamp"
  backupRoot = $backupRoot
  entryCount = $entries.Count
  skippedCount = $skipped.Count
  driveMirrored = $driveOk
  drivePath = $drivePath
  manifest = $manifestPath
}
$result | ConvertTo-Json -Depth 5
