# Windows installer for task-completion-detector
# Similar to install.sh

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonDir = Join-Path $ScriptDir "python"
$TaskWatchScript = Join-Path $ScriptDir "task-watch.ps1"

Write-Host "[INFO] Installing task-completion-detector..." -ForegroundColor Cyan

# Create launchers directory
$LauncherDir = Join-Path $ScriptDir "launchers"
if (-not (Test-Path $LauncherDir)) {
    New-Item -ItemType Directory -Path $LauncherDir -Force | Out-Null
}

# Step 1: Find Python
$PythonBin = $null
$PythonCandidates = @("python", "python3", "py -3")

foreach ($candidate in $PythonCandidates) {
    try {
        $version = & cmd /c "$candidate --version 2>&1"
        if ($version -match "Python 3") {
            $PythonBin = $candidate
            Write-Host "Found Python: $version" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $PythonBin) {
    Write-Host "[ERROR] Python 3 not found. Please install Python 3.9+ and ensure it is in your PATH." -ForegroundColor Red
    exit 1
}

# Step 2: Create virtual environment
Push-Location $PythonDir

$VenvPath = Join-Path $PythonDir ".venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

# Check if venv exists and is valid (has Scripts folder on Windows)
if ((Test-Path $VenvPath) -and -not (Test-Path $ActivateScript)) {
    Write-Host "Removing invalid virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $VenvPath
}

if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    if ($PythonBin -eq "py -3") {
        & py -3 -m venv .venv
    } else {
        & $PythonBin -m venv .venv
    }
    
    # Verify venv was created correctly
    if (-not (Test-Path $ActivateScript)) {
        Write-Host "[ERROR] Failed to create virtual environment. Please check your Python installation." -ForegroundColor Red
        Pop-Location
        exit 1
    }
}

# Activate venv and install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
. $ActivateScript
pip install -q -r ..\requirements.txt

# Step 3: Create Desktop shortcut
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "task-watch.lnk"

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$TaskWatchScript`""
    $Shortcut.WorkingDirectory = $ScriptDir
    $Shortcut.Description = "Task Completion Detector"
    $Shortcut.Save()
    Write-Host "Created Desktop shortcut: task-watch.lnk" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Could not create Desktop shortcut: $_" -ForegroundColor Yellow
}

# Step 4: Add global 'task-watch' command to PowerShell profile
$ProfileDir = Split-Path -Parent $PROFILE
if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
}

$AliasLine = "Set-Alias task-watch `"$TaskWatchScript`""
$ProfileExists = Test-Path $PROFILE
$AliasExists = $false

if ($ProfileExists) {
    $ProfileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
    if ($ProfileContent -match "task-watch") {
        $AliasExists = $true
    }
}

if (-not $AliasExists) {
    Write-Host ""
    Write-Host "To use 'task-watch' command globally, we need to add an alias to your PowerShell profile." -ForegroundColor Cyan
    $AddAlias = Read-Host "Add 'task-watch' command to PowerShell profile? (Y/n)"
    if ($AddAlias -ne "n" -and $AddAlias -ne "N") {
        # Add alias to profile
        Add-Content -Path $PROFILE -Value ""
        Add-Content -Path $PROFILE -Value "# Task Completion Detector"
        Add-Content -Path $PROFILE -Value $AliasLine
        Write-Host "Added 'task-watch' alias to PowerShell profile." -ForegroundColor Green
        Write-Host "Restart your terminal or run: . `$PROFILE" -ForegroundColor Yellow
    }
} else {
    Write-Host "'task-watch' alias already exists in PowerShell profile." -ForegroundColor Green
}

# Step 5: Run guided configuration
Write-Host ""
Write-Host "Starting guided configuration setup..." -ForegroundColor Cyan
python main.py setup-config

Pop-Location

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "[OK] Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage (after restarting terminal):" -ForegroundColor White
Write-Host "  task-watch           - Monitor last selected default region" -ForegroundColor Gray
Write-Host "  task-watch -r        - Select region and start monitoring" -ForegroundColor Gray
Write-Host "  task-watch -c        - (Re)run guided configuration" -ForegroundColor Gray
Write-Host "  task-watch -u        - Update to latest version" -ForegroundColor Gray
Write-Host ""
Write-Host "  Or double-click task-watch.lnk on your Desktop" -ForegroundColor Gray
Write-Host "===============================================================" -ForegroundColor Cyan
