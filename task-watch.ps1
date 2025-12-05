# Main launcher script for task-completion-detector on Windows
# Similar to task-watch.sh

param(
    [Alias("r", "select")]
    [switch]$SelectRegion,
    
    [Alias("c", "setup-config", "edit-config")]
    [switch]$Config,
    
    [Alias("u")]
    [switch]$Update,
    
    [Alias("h")]
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir
$DefaultRegionName = "windsurf_panel"

function Show-Usage {
    Write-Host @"
Usage: task-watch.ps1 [OPTION]

  (no option)            Monitor the last selected default region ($DefaultRegionName).
  -SelectRegion, -r      Select a region and then start monitoring it.
  -Config, -c            Run the guided configuration / config editor.
  -Update, -u            Update the task-completion-detector git clone (if available) and exit.
  -Help, -h              Show this help.

Notes:
- The default region name is "$DefaultRegionName". The first selection run stores it there.
"@
}

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
    
    # Create venv if missing
    $VenvPath = Join-Path (Get-Location) ".venv"
    if (-not (Test-Path $VenvPath)) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        if ($PythonBin -eq "py") {
            & py -3 -m venv .venv
        } else {
            & $PythonBin -m venv .venv
        }
    }
    
    # Activate venv
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    . $ActivateScript
    
    # Install/update dependencies
    pip install -q -r ..\requirements.txt
}

function Invoke-Update {
    $GitDir = Join-Path $ProjectRoot ".git"
    if (-not (Test-Path $GitDir)) {
        Write-Host "No .git directory found at $ProjectRoot. Auto-update requires a git clone." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Updating task-completion-detector in $ProjectRoot..." -ForegroundColor Cyan
    Push-Location $ProjectRoot
    try {
        git pull --ff-only
    } catch {
        Write-Host "Warning: git pull failed (non-fast-forward or error)." -ForegroundColor Yellow
        Pop-Location
        exit 1
    }
    Pop-Location
    
    Write-Host "Code update complete. Refreshing Python environment..." -ForegroundColor Green
    Initialize-PythonEnv
    Write-Host "Python environment refreshed. Update finished." -ForegroundColor Green
    Pop-Location
}

# Main logic
if ($Help) {
    Show-Usage
    exit 0
}

if ($Update) {
    Invoke-Update
    exit 0
}

if ($SelectRegion) {
    Initialize-PythonEnv
    python main.py select-region --name $DefaultRegionName
    if ($LASTEXITCODE -eq 0) {
        python main.py monitor --name $DefaultRegionName
    }
    Pop-Location
    exit $LASTEXITCODE
}

if ($Config) {
    Initialize-PythonEnv
    python main.py setup-config
    Pop-Location
    exit $LASTEXITCODE
}

# Default: watch mode
Initialize-PythonEnv
python main.py monitor --name $DefaultRegionName
Pop-Location
exit $LASTEXITCODE
