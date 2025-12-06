# Wrapper script for change-watch mode on Windows
# This script directly calls the Python CLI to avoid argument forwarding issues

param(
    [switch]$SelectRegion,
    [switch]$select,
    [switch]$r,
    [switch]$s,
    
    [switch]$Config,
    [switch]$c,
    
    [switch]$Update,
    [switch]$u,
    
    [switch]$Help,
    [switch]$h,
    
    [string]$RegionName
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir

function Initialize-PythonEnv {
    Push-Location (Join-Path $ProjectRoot "python")
    
    # Find Python
    $PythonBin = $null
    $PythonCandidates = @("python", "python3")
    
    foreach ($candidate in $PythonCandidates) {
        try {
            $version = & $candidate --version 2>&1
            if ($version -match "Python 3") {
                $PythonBin = $candidate
                break
            }
        } catch {
            continue
        }
    }
    
    if (-not $PythonBin) {
        # Try py launcher
        try {
            $version = & py -3 --version 2>&1
            if ($version -match "Python 3") {
                $PythonBin = "py"
            }
        } catch {}
    }
    
    if (-not $PythonBin) {
        Write-Host "[ERROR] Python 3 not found. Please install Python 3.9+ and ensure it is in your PATH." -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    # Create venv if missing or invalid
    $VenvPath = Join-Path (Get-Location) ".venv"
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    
    # Check if venv exists and is valid (has Scripts folder on Windows)
    if ((Test-Path $VenvPath) -and -not (Test-Path $ActivateScript)) {
        Write-Host "Removing invalid virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvPath
    }
    
    if (-not (Test-Path $VenvPath)) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        if ($PythonBin -eq "py") {
            & py -3 -m venv .venv
        } else {
            & $PythonBin -m venv .venv
        }
        
        # Verify venv was created correctly
        if (-not (Test-Path $ActivateScript)) {
            Write-Host "[ERROR] Failed to create virtual environment." -ForegroundColor Red
            Pop-Location
            exit 1
        }
    }
    
    # Activate venv
    . $ActivateScript
    
    # Install/update dependencies
    pip install -q -r ..\requirements.txt
}

function Test-UpdateAvailable {
    $GitDir = Join-Path $ProjectRoot ".git"
    if (-not (Test-Path $GitDir)) {
        return
    }

    Push-Location $ProjectRoot
    try {
        git remote update | Out-Null
        # Use explicit refs to avoid PowerShell interpreting '@' and '@{u}'
        $local  = git rev-parse HEAD
        $remote = git rev-parse '@{u}'
        $base   = git merge-base HEAD '@{u}'
    } catch {
        Pop-Location
        return
    }
    Pop-Location

    # Remote is ahead of local (fast-forward available): notify user once
    if (($local -eq $base) -and ($remote -ne $local)) {
        Write-Host "[Update available] A newer version is available. Run 'task-watch -u' to update." -ForegroundColor Yellow
    }
}

# Main execution
if ($Update -or $u) {
    # Delegate update behavior to task-watch.ps1 so semantics stay in one place
    & (Join-Path $ProjectRoot "task-watch.ps1") -u
    exit $LASTEXITCODE
}

Test-UpdateAvailable

if ($Help -or $h) {
    Write-Host "Usage: change-watch [-r] [-s] [-Config|-c] [RegionName]" -ForegroundColor Cyan
    Write-Host "  (no option)        Monitor the last selected default region for changes."
    Write-Host "  RegionName         Monitor the named region for changes."
    Write-Host "  -SelectRegion,-r,-s  Select a region and then start monitoring it for changes."
    Write-Host "  -Config,-c         Run the guided configuration / config editor."
    return
}

if ($Config -or $c) {
    Initialize-PythonEnv
    python main.py setup-config
    Pop-Location
    exit $LASTEXITCODE
}

Initialize-PythonEnv

$regionName = if ($RegionName) { $RegionName } else { "default" }

if ($SelectRegion -or $select -or $r -or $s) {
    # Select region first
    python main.py select-region --name $regionName
    if ($LASTEXITCODE -ne 0) {
        Pop-Location
        exit $LASTEXITCODE
    }
}

# Then monitor for changes
python main.py monitor --name $regionName --change

Pop-Location