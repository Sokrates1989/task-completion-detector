# Wrapper script for change-watch mode on Windows
# This script invokes task-watch.ps1 with the -Change flag

param(
    [switch]$SelectRegion,
    [switch]$select,
    [switch]$r,
    [switch]$s,
    
    [switch]$Update,
    [switch]$u,
    
    [switch]$Help,
    [switch]$h,
    
    [string]$RegionName
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskWatchScript = Join-Path $ScriptDir "task-watch.ps1"

# Build arguments to forward
$ForwardArgs = @("-Change")

if ($SelectRegion -or $select -or $r -or $s) { $ForwardArgs += "-r" }
if ($Update -or $u) { $ForwardArgs += "-u" }
if ($Help -or $h) { $ForwardArgs += "-h" }
if ($RegionName) { $ForwardArgs += "-RegionName"; $ForwardArgs += $RegionName }

& $TaskWatchScript @ForwardArgs
