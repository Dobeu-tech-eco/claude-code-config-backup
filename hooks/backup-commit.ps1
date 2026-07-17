# backup-commit.ps1 — scheduled auto-backup of ~/.claude config (fail-open).
# Commits any changes to the local git repo; pushes only if an 'origin'
# remote is configured. Safe to run before a remote exists. Logs to
# hooks\backup-commit.log (gitignored). Never throws — backup must not
# interrupt anything.

$ErrorActionPreference = 'Continue'
$repo = 'C:\Users\JeremyWilliams\.claude'
$log  = Join-Path $repo 'hooks\backup-commit.log'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

function Note($m) { try { Add-Content -LiteralPath $log -Value "[$stamp] $m" } catch {} }

try {
    if (-not (Test-Path (Join-Path $repo '.git'))) { Note 'no git repo — skipped'; exit 0 }

    & git -C $repo add -A 2>&1 | Out-Null

    # Anything staged?
    & git -C $repo diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { Note 'no changes'; exit 0 }

    $msg = "chore: scheduled backup $stamp"
    & git -C $repo commit -q -m $msg 2>&1 | Out-Null
    Note "committed: $msg"

    # Push only if an origin remote exists (fail-open on network/auth issues)
    $hasOrigin = (& git -C $repo remote 2>$null) -contains 'origin'
    if ($hasOrigin) {
        & git -C $repo push origin HEAD 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Note 'pushed to origin' } else { Note 'push failed (kept local commit)' }
    } else {
        Note 'no origin remote — local commit only'
    }
}
catch { Note "error: $_" }
exit 0
