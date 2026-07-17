#Requires -Version 7.0
<#
    Claude Code Developer Status Line (PowerShell 7 port of statusline-developer.sh)

    Reads the Claude Code status JSON blob on STDIN and prints a single line:
        <model_display_name> <output_style> <project>/<relpath> (<branch> +staged ~modified ?untracked) [HH:MM]

    Colors (dimmed): cyan model, magenta output style, blue path,
    yellow git-when-dirty / green git-when-clean, grey time.

    Hard requirement: this must NEVER throw and NEVER write to stderr -- a status line
    that errors breaks the TUI. Everything is wrapped defensively.
#>

$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference    = 'SilentlyContinue'

$ESC = [char]27

function Get-GitOutput {
    # Runs git in $Directory, swallowing stderr and any launch failure (git absent, not a repo).
    param([string]$Directory, [string[]]$GitArgs)
    try {
        $out = & git -C $Directory @GitArgs 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        if ($null -eq $out) { return $null }
        return ($out -join "`n")
    } catch {
        return $null
    }
}

try {
    # ---- Read + parse stdin ------------------------------------------------
    $raw = [Console]::In.ReadToEnd()

    $json = $null
    if (-not [string]::IsNullOrWhiteSpace($raw)) {
        try { $json = $raw | ConvertFrom-Json } catch { $json = $null }
    }

    $modelName   = 'Claude'
    $outputStyle = 'default'
    $currentDir  = ''
    $projectDir  = ''

    if ($json) {
        if ($json.model.display_name)  { $modelName   = [string]$json.model.display_name }
        if ($json.output_style.name)   { $outputStyle = [string]$json.output_style.name }
        if ($json.workspace.current_dir) { $currentDir = [string]$json.workspace.current_dir }
        if ($json.workspace.project_dir) { $projectDir = [string]$json.workspace.project_dir }
    }

    if ([string]::IsNullOrWhiteSpace($currentDir)) { $currentDir = (Get-Location).Path }

    # ---- Display path ------------------------------------------------------
    # <project-basename>/<path relative to project_dir>, or just the basename
    # of current_dir when there is no project or we're already at its root.
    $displayPath = Split-Path -Path $currentDir -Leaf

    if (-not [string]::IsNullOrWhiteSpace($projectDir)) {
        $curFull  = $currentDir
        $projFull = $projectDir
        try { $curFull  = [System.IO.Path]::GetFullPath($currentDir) } catch { }
        try { $projFull = [System.IO.Path]::GetFullPath($projectDir) } catch { }

        $curNorm  = $curFull.TrimEnd('\', '/')
        $projNorm = $projFull.TrimEnd('\', '/')
        $projLeaf = Split-Path -Path $projNorm -Leaf

        if ($curNorm -ieq $projNorm) {
            # At the project root: show just the project name.
            if ($projLeaf) { $displayPath = $projLeaf }
        } else {
            $rel = $null
            try { $rel = [System.IO.Path]::GetRelativePath($projNorm, $curNorm) } catch { $rel = $null }

            if ([string]::IsNullOrWhiteSpace($rel) -or $rel -eq '.') {
                if ($projLeaf) { $displayPath = $projLeaf }
            } elseif ($rel.StartsWith('..') -or [System.IO.Path]::IsPathRooted($rel)) {
                # current_dir is outside the project tree -- fall back to its basename.
                $displayPath = Split-Path -Path $curNorm -Leaf
            } else {
                $rel = $rel -replace '\\', '/'
                $displayPath = "$projLeaf/$rel"
            }
        }
    }

    # ---- Git segment -------------------------------------------------------
    $gitInfo = ''
    $insideRepo = Get-GitOutput -Directory $currentDir -GitArgs @('rev-parse', '--git-dir')

    if ($insideRepo) {
        $branch = Get-GitOutput -Directory $currentDir -GitArgs @('symbolic-ref', '--short', 'HEAD')
        if ([string]::IsNullOrWhiteSpace($branch)) {
            $branch = Get-GitOutput -Directory $currentDir -GitArgs @('rev-parse', '--short', 'HEAD')
        }
        if ([string]::IsNullOrWhiteSpace($branch)) { $branch = 'detached' }
        $branch = $branch.Trim()

        $staged = 0; $modified = 0; $untracked = 0
        $status = Get-GitOutput -Directory $currentDir -GitArgs @('status', '--porcelain')
        if (-not [string]::IsNullOrWhiteSpace($status)) {
            foreach ($line in ($status -split "`n")) {
                if ([string]::IsNullOrEmpty($line)) { continue }
                if ($line -match '^\?\?')      { $untracked++; continue }
                if ($line -match '^[MADRC]')   { $staged++ }
                if ($line -match '^.M')        { $modified++ }
            }
        }

        $parts = @()
        if ($staged    -gt 0) { $parts += "+$staged" }
        if ($modified  -gt 0) { $parts += "~$modified" }
        if ($untracked -gt 0) { $parts += "?$untracked" }

        if ($parts.Count -gt 0) {
            $gitInfo = " $ESC[33m($branch $($parts -join ' '))$ESC[0m"
        } else {
            $gitInfo = " $ESC[32m($branch)$ESC[0m"
        }
    }

    # ---- Time --------------------------------------------------------------
    $now = (Get-Date).ToString('HH:mm')

    # ---- Emit --------------------------------------------------------------
    $line = "$ESC[2;36m$modelName$ESC[0m " +
            "$ESC[2;35m$outputStyle$ESC[0m " +
            "$ESC[2;34m$displayPath$ESC[0m" +
            "$gitInfo " +
            "$ESC[2;37m[$now]$ESC[0m"

    [Console]::Out.Write($line)
} catch {
    # Last-resort fallback: never fail, never touch stderr.
    try { [Console]::Out.Write("Claude") } catch { }
}
