# Installation & configuration

## Prerequisites

- **macOS** or **Windows 10/11** with Python 3.9+
- Git
- Optional: Telegram account (for Telegram notifications)
- Optional: SMTP email account (for email notifications)

---

## Option 1: Quick install (recommended)

### 🍎 macOS

If you want the default setup with Desktop shortcuts and a global `task-watch` command (plus legacy `ai-select` / `ai-watch` aliases), run:

```bash
ORIGINAL_DIR=$(pwd)
mkdir -p /tmp/task-detector-setup && cd /tmp/task-detector-setup
curl -sO https://raw.githubusercontent.com/Sokrates1989/task-completion-detector/main/setup/macos.sh
bash macos.sh
cd "$ORIGINAL_DIR"
rm -rf /tmp/task-detector-setup
```

What this does:

- Downloads `setup/macos.sh` from this repository.
- Clones `task-completion-detector` into `~/tools/task-completion-detector` (or updates it if already cloned).
- Runs `./install.sh` inside that directory, which:
  - Creates a `task-watch` launcher and, if possible, symlinks it into `/usr/local/bin`.
  - Also creates backward-compatible `ai-select` / `ai-watch` aliases that forward to `task-watch`.
  - Creates double-clickable `task-watch.command`, `ai-select.command` and `ai-watch.command` files on your Desktop.
  - Creates a Python virtual environment under `python/.venv` and installs the required packages.
  - Starts a guided configuration wizard to set up monitoring defaults and notification channels.
  - Fixes ownership of the `config` directory when run with `sudo` so your normal user can edit it.

After this finishes you should be able to:

- From Terminal: run `task-watch` as the main entrypoint:
  - `task-watch --select-region` to select a region and start monitoring immediately.
  - `task-watch` to reuse the last selected default region.
  - `task-watch --config` to rerun the guided configuration / config editor.
- `ai-select` and `ai-watch` are provided as backward-compatible aliases for the same behaviors.
- From Finder: double-click `task-watch.command`, `ai-select.command` or `ai-watch.command` on your Desktop.

> macOS will ask for *Screen Recording* permission the first time you capture the screen. Grant it so the tool can watch your AI window.

### 🪟 Windows

Run in PowerShell (as Administrator for best results):

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

What this does:

- Downloads `setup/windows.ps1` from this repository.
- Clones `task-completion-detector` into `%USERPROFILE%\tools\task-completion-detector` (or updates it if already cloned).
- Runs `install.ps1` inside that directory, which:
  - Creates a Python virtual environment under `python\.venv` and installs the required packages.
  - Creates a `task-watch.lnk` shortcut on your Desktop.
  - Optionally adds the install directory to your user PATH.
  - Starts a guided configuration wizard to set up monitoring defaults and notification channels.

After this finishes you should be able to:

- From PowerShell (after restarting terminal):
  - `task-watch -r` to select a region and start monitoring immediately.
  - `task-watch` to reuse the last selected default region.
  - `task-watch -c` to rerun the guided configuration / config editor.
  - `task-watch -u` to update to the latest version.
- From Desktop: double-click `task-watch.lnk`.

> For enhanced Windows toast notifications, optionally install BurntToast:
> `Install-Module -Name BurntToast -Scope CurrentUser`

---

## Option 2: Manual install

### 🍎 macOS

1. Clone the repository:

   ```bash
   git clone https://github.com/Sokrates1989/task-completion-detector.git
   cd task-completion-detector
   ```

2. Make sure the installer is executable and run it:

   ```bash
   chmod +x install.sh
   ./install.sh
   ```

   This performs the same steps as in the quick install (virtualenv, launchers, guided config, etc.).

3. To rerun the guided configuration later:

   ```bash
   cd python
   # (optional but recommended) source .venv/bin/activate
   python main.py setup-config
   ```

### 🪟 Windows

1. Clone the repository:

   ```powershell
   git clone https://github.com/Sokrates1989/task-completion-detector.git
   cd task-completion-detector
   ```

2. Run the installer:

   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
   .\install.ps1
   ```

   This performs the same steps as in the quick install (virtualenv, launchers, guided config, etc.).

3. To rerun the guided configuration later:

   ```powershell
   cd python
   ..\.venv\Scripts\Activate.ps1
   python main.py setup-config
   ```

---

## Troubleshooting

### macOS

- **Cannot create `/usr/local/bin` symlinks:**
  - Run `./install.sh` with `sudo` if you want global `task-watch` (and alias) commands.
  - The script will attempt to fix the ownership of the `config` directory back to your normal user.

- **No macOS notification appears:**
  - Notifications are sent via the built-in `osascript display notification` mechanism.
  - Check System Settings → Notifications, locate your terminal app (or iTerm), and allow alerts/banners.

- **Screen Recording permission denied:**
  - Go to System Settings → Privacy & Security → Screen Recording.
  - Enable access for your terminal app (or whichever app you used to run `ai-select` / `ai-watch`).

### Windows

- **PowerShell execution policy error:**
  - Run `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force` before running the scripts.
  - Or run PowerShell as Administrator.

- **No Windows notification appears:**
  - Check that Focus Assist is not blocking notifications.
  - Open Action Center (Win+A) to see if the notification was delivered silently.
  - For better notifications, install BurntToast: `Install-Module -Name BurntToast -Scope CurrentUser`

- **Python not found:**
  - Install Python 3.9+ from https://www.python.org/downloads/
  - Make sure to check "Add Python to PATH" during installation.

For more details on how the tool behaves at runtime, see `docs/USAGE.md`.
