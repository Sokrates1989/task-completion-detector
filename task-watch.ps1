# Main launcher script for task-completion-detector on Windows
# Similar to task-watch.sh

param(
    [switch]$SelectRegion,
    [switch]$select,
    [switch]$r,
    [switch]$s,
    
    [switch]$Change,
    [switch]$WatchChange,
    [switch]$w,
    
    [switch]$Config,
    [switch]$setup_config,
    [switch]$edit_config,
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
$DefaultRegionName = "default"

# Import helper functions (Initialize-PythonEnv, Invoke-ConfigScreenshotMigration, Invoke-Update, Test-UpdateAvailable)
$helpersPath = Join-Path $ProjectRoot "setup\modules\task-watch-helpers.ps1"
if (Test-Path $helpersPath) {
    . $helpersPath
}

function Show-Usage {
    Write-Host @"
Usage: task-watch.ps1 [OPTION] [RegionName]

  (no option)            Monitor the last selected default region ($DefaultRegionName).
  RegionName             Monitor the named region.
  -SelectRegion, -r, -s  Select a region and then start monitoring it (optionally naming it).
  -Change, -w            Advanced: watch for changes instead of stability (used by change-watch).
  -Config, -c, --setup-config, --edit-config
                        Run the guided configuration / config editor.
  -Update, -u            Update the task-completion-detector git clone (if available) and exit.
  -Help, -h              Show this help.

Notes:
- The default region name is "$DefaultRegionName". The first selection run stores it there.
"@
}

## Helper functions (Initialize-PythonEnv, Invoke-ConfigScreenshotMigration, Invoke-Update, Test-UpdateAvailable)
## are defined in setup\modules\task-watch-helpers.ps1 and imported above.

# Main logic
if ($Help -or $h) {
    Show-Usage
    exit 0
}

if ($Update -or $u) {
    Invoke-Update
    exit 0
}

Test-UpdateAvailable

if ($SelectRegion -or $select -or $r -or $s) {
    Initialize-PythonEnv
    $targetName = if ($RegionName) { $RegionName } else { $DefaultRegionName }
    $changeFlag = if ($Change -or $WatchChange -or $w) { "--change" } else { "" }
    if ($RegionName) {
        python main.py select-region --name $targetName --also-name $DefaultRegionName
    } else {
        python main.py select-region --name $DefaultRegionName
    }
    if ($LASTEXITCODE -eq 0) {
        if ($changeFlag) {
            python main.py monitor --name $targetName $changeFlag
        } else {
            python main.py monitor --name $targetName
        }
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
$targetName = if ($RegionName) { $RegionName } else { $DefaultRegionName }
$changeFlag = if ($Change -or $WatchChange -or $w) { "--change" } else { "" }
if ($changeFlag) {
    python main.py monitor --name $targetName $changeFlag
} else {
    python main.py monitor --name $targetName
}
Pop-Location
exit $LASTEXITCODE
