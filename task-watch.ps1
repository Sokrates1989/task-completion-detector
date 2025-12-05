# Main launcher script for task-completion-detector on Windows
# Similar to task-watch.sh

param(
    [switch]$SelectRegion,
    [switch]$select,
    [switch]$r,
    
    [switch]$Config,
    [switch]$setup_config,
    [switch]$edit_config,
    [switch]$c,
    
    [switch]$Update,
    [switch]$u,
    
    [switch]$Help,
    [switch]$h
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
if ($Help -or $h) {
    Show-Usage
    exit 0
}

if ($Update -or $u) {
    Invoke-Update
    exit 0
}

if ($SelectRegion -or $select -or $r) {
    Initialize-PythonEnv
    python main.py select-region --name $DefaultRegionName
    if ($LASTEXITCODE -eq 0) {
        python main.py monitor --name $DefaultRegionName
    }
    Pop-Location
    exit $LASTEXITCODE
}

if ($Config -or $setup_config -or $edit_config -or $c) {
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
