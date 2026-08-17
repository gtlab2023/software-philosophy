[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("project-control-session-start", "project-control-stop")]
    [string]$Event
)

$ErrorActionPreference = "Stop"

$pluginRoot = $env:CLAUDE_PLUGIN_ROOT
if (-not $pluginRoot) {
    $pluginRoot = $env:PLUGIN_ROOT
}
if (-not $pluginRoot) {
    $pluginRoot = Split-Path -Parent $PSScriptRoot
}

$candidates = @()
if ($env:SOFTWARE_PHILOSOPHY_PYTHON) {
    $candidates += [PSCustomObject]@{ Command = $env:SOFTWARE_PHILOSOPHY_PYTHON; PrefixArgs = @() }
}
$candidates += [PSCustomObject]@{ Command = "py"; PrefixArgs = @("-3") }
$candidates += [PSCustomObject]@{ Command = "python3"; PrefixArgs = @() }
$candidates += [PSCustomObject]@{ Command = "python"; PrefixArgs = @() }

$selectedCommand = $null
$selectedPrefixArgs = @()
foreach ($candidate in $candidates) {
    $resolved = Get-Command -Name $candidate.Command -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $resolved) {
        continue
    }
    $prefixArgs = @($candidate.PrefixArgs)
    try {
        & $resolved.Source @prefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" *> $null
        $versionExitCode = $LASTEXITCODE
    }
    catch {
        $versionExitCode = 1
    }
    if ($versionExitCode -eq 0) {
        $selectedCommand = $resolved.Source
        $selectedPrefixArgs = $prefixArgs
        break
    }
}

if ($selectedCommand) {
    $coordinator = Join-Path $pluginRoot "hooks/coordinator.py"
    & $selectedCommand @selectedPrefixArgs $coordinator --event $Event
    exit $LASTEXITCODE
}

$configPath = Join-Path (Get-Location) ".project-control.json"
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    $git = Get-Command -Name "git" -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($git) {
        try {
            $repoRoot = (& $git.Source rev-parse --show-toplevel 2>$null | Select-Object -First 1)
            if ($LASTEXITCODE -eq 0 -and $repoRoot) {
                $configPath = Join-Path $repoRoot ".project-control.json"
            }
        }
        catch {
            $repoRoot = $null
        }
    }
}

$configured = $false
if (Test-Path -LiteralPath $configPath -PathType Leaf) {
    try {
        $configText = Get-Content -LiteralPath $configPath -Raw
        $configured = $configText -match '"enabled"\s*:\s*true'
    }
    catch {
        $configured = $false
    }
}

$response = @{ "continue" = $true }
if ($configured) {
    $response["systemMessage"] = "Project-control hook skipped: Python 3.10+ is unavailable. Install Python, or set SOFTWARE_PHILOSOPHY_PYTHON to a compatible interpreter."
}
$response | ConvertTo-Json -Compress
exit 0
