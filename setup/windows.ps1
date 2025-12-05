# Windows setup script for task-completion-detector
# Similar to setup/macos.sh

$ErrorActionPreference = "Stop"

$TargetDir = "$env:USERPROFILE\tools\task-completion-detector"
$RepoUrl = "https://github.com/Sokrates1989/task-completion-detector.git"

Write-Host "➡️ Installing task-completion-detector into $TargetDir" -ForegroundColor Cyan

# Step 1: Clone or update the repository
if (-not (Test-Path "$TargetDir\.git")) {
    Write-Host "Cloning repository..." -ForegroundColor Yellow
    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }
    Push-Location $TargetDir
    git clone $RepoUrl .
    Pop-Location
} else {
    Write-Host "ℹ️ task-completion-detector already cloned – attempting to update..." -ForegroundColor Yellow
    Push-Location $TargetDir
    try {
        git pull --ff-only
    } catch {
        Write-Host "⚠️ Could not fast-forward; continuing with existing clone." -ForegroundColor Yellow
    }
    Pop-Location
}

# Step 2: Run the installer
Write-Host "🔧 Running installer..." -ForegroundColor Cyan
Push-Location $TargetDir
& .\install.ps1
Pop-Location

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
