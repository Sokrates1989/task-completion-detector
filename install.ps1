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
if (-not (Test-Path $VenvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    if ($PythonBin -eq "py -3") {
        & py -3 -m venv .venv
    } else {
        & $PythonBin -m venv .venv
    }
}

# Activate venv and install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
. $ActivateScript
pip install -r ..\requirements.txt

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

# Step 4: Add to PATH (optional, user-level)
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$ScriptDir*") {
    $AddToPath = Read-Host "Add task-completion-detector to your PATH? (y/N)"
    if ($AddToPath -eq "y" -or $AddToPath -eq "Y") {
        [Environment]::SetEnvironmentVariable("Path", "$UserPath;$ScriptDir", "User")
        Write-Host "Added $ScriptDir to user PATH. Restart your terminal for changes to take effect." -ForegroundColor Green
    }
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
Write-Host "Usage:" -ForegroundColor White
Write-Host "  From PowerShell:" -ForegroundColor Gray
Write-Host "    .\task-watch.ps1                 - Monitor last selected default region" -ForegroundColor Gray
Write-Host "    .\task-watch.ps1 --select-region - Select region and start monitoring" -ForegroundColor Gray
Write-Host "    .\task-watch.ps1 --config        - (Re)run guided configuration" -ForegroundColor Gray
Write-Host "    .\task-watch.ps1 --update        - Update to latest version" -ForegroundColor Gray
Write-Host ""
Write-Host "  From Desktop: Double-click task-watch.lnk" -ForegroundColor Gray
Write-Host "===============================================================" -ForegroundColor Cyan
