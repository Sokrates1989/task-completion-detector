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

function Invoke-ConfigScreenshotMigration {
    $configPath = Join-Path $ProjectRoot "config\config.txt"

    if (-not (Test-Path $configPath)) {
        return
    }

    try {
        $raw = Get-Content -Path $configPath -Raw -ErrorAction Stop
        $cfg = $raw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        Write-Host "[WARN] Could not parse config at $configPath for migration; skipping screenshot migration." -ForegroundColor Yellow
        return
    }

    if (-not $cfg.notifications) {
        return
    }

    $notif = $cfg.notifications
    $hasProp = $notif.PSObject.Properties.Name -contains "includeScreenshotInTelegram"
    if ($hasProp) {
        return
    }

    Write-Host "" 
    Write-Host "Your config was created before Telegram screenshot support was added." -ForegroundColor Cyan

    $enable = $false
    while ($true) {
        $answer = Read-Host "Enable sending screenshots in Telegram notifications? [y/N]"
        if (-not $answer) {
            $enable = $false
            break
        }
        $lower = $answer.ToLower()
        if ($lower -eq "y" -or $lower -eq "yes") {
            $enable = $true
            break
        }
        if ($lower -eq "n" -or $lower -eq "no") {
            $enable = $false
            break
        }
        Write-Host "Please answer y or n."
    }

    $value = $enable
    Add-Member -InputObject $notif -MemberType NoteProperty -Name "includeScreenshotInTelegram" -Value $value

    try {
        $cfg | ConvertTo-Json -Depth 10 | Set-Content -Path $configPath -Encoding UTF8
        Write-Host "Config updated: notifications.includeScreenshotInTelegram = $value" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Failed to write updated config to $configPath" -ForegroundColor Yellow
    }
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
    Write-Host "Python environment refreshed." -ForegroundColor Green

    Invoke-ConfigScreenshotMigration

    Write-Host "Update finished." -ForegroundColor Green
    Pop-Location
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
        Write-Host "[Update available] A newer version of task-completion-detector is available. Run 'task-watch -u' to update." -ForegroundColor Yellow
    }
}
