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

### Select region + start watching

**macOS:**
```bash
task-watch --select-region
# or: task-watch --select
# or: task-watch -r
```

**Windows (PowerShell, after install):**
```powershell
task-watch -r
# or: task-watch -SelectRegion
```

This opens the region selector, saves the region as the default, and immediately starts monitoring.

### Watch last selected region

**macOS:**
```bash
task-watch
```

**Windows (PowerShell, after install):**
```powershell
task-watch
```

Reuse the last selected default region and start monitoring it again.

### Edit configuration (monitor + notifications)

**macOS:**
```bash
task-watch --config
```

**Windows (PowerShell, after install):**
```powershell
task-watch -c
# or: task-watch -Config
```

Reruns the guided configuration wizard so you can change:

- Monitor thresholds (interval, stableSecondsThreshold, differenceThreshold)
- Notification channels (Telegram, email, local notifications) and their credentials

### Update to latest version (git clone only)

**macOS:**
```bash
task-watch --update
```

**Windows (PowerShell, after install):**
```powershell
task-watch -u
# or: task-watch -Update
```

Runs a `git pull --ff-only` in the installation directory (when it is a git clone) and exits.

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
