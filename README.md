# task-completion-detector
Get notified when your AI coding assistant needs you. Never miss a task completion or required input again.

## 🚀 Quick Install

### macOS

Copy and run in your terminal:

```bash
ORIGINAL_DIR=$(pwd)
mkdir -p /tmp/task-detector-setup && cd /tmp/task-detector-setup
curl -sO https://raw.githubusercontent.com/Sokrates1989/task-completion-detector/main/setup/macos.sh
bash macos.sh
cd "$ORIGINAL_DIR"
rm -rf /tmp/task-detector-setup
```

### Windows

Copy and run in PowerShell (as Administrator for best results):

```powershell
$OriginalDir = Get-Location
$TempDir = "$env:TEMP\task-detector-setup"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
Set-Location $TempDir
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Sokrates1989/task-completion-detector/main/setup/windows.ps1" -OutFile "windows.ps1"
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
.\windows.ps1
Set-Location $OriginalDir
Remove-Item -Recurse -Force $TempDir
```

## 📖 Quick usage

For all commands and detailed behavior, see `docs/USAGE.md`.

### macOS (Terminal)

```bash
task-watch --select-region [name]   # select & watch region (aliases: --select, -r, -s; also saves under default name)
task-watch [name]                   # watch named region (or default when omitted)
task-watch --config                 # open config wizard (monitor thresholds, notifications)
task-watch --update                 # update to latest version (git clone only)
```

### Windows (PowerShell, after install)

```powershell
task-watch -r [name]                # select & watch region (also -s, -SelectRegion; also saves under default name)
task-watch [name]                   # watch named region (or default when omitted)
task-watch -c                       # open config wizard (also -Config)
task-watch -u                       # update to latest version (also -Update; git clone only)
```

### Desktop shortcuts

- **macOS:** Double-click `task-watch.command` on your Desktop
- **Windows:** Double-click `task-watch.lnk` on your Desktop

**Legacy aliases (macOS only):**
- `ai-select` behaves like `task-watch --select-region`
- `ai-watch` behaves like `task-watch`

## 📚 More docs

- **Installation & configuration details:** `docs/INSTALL.md`
- **Usage, behavior & Telegram setup:** `docs/USAGE.md`

## 💻 Supported Platforms

- **macOS** (tested) - Uses `osascript` for native notifications
- **Windows** (tested) - Uses PowerShell toast notifications (optionally via BurntToast module)
