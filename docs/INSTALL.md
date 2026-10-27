# Installation & configuration

## Prerequisites

- **macOS** or **Windows 10/11** with Python 3.9+
- **macOS:** Python must use OpenSSL 1.1.1 or newer. Install a Python build from [python.org](https://www.python.org/downloads/macos/) or Homebrew (`brew install python`). Apple's LibreSSL-based system Python is unsuitable for the application's HTTP dependencies.
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

- **Saved region is outside the connected displays / `UnidentifiedImageError`:**
  - A saved region can become unavailable after disconnecting a monitor or changing the display arrangement.
  - Run `task-watch --select-region` (or `task-watch --select-region name` for a named region), then follow the mouse-position prompts to save a visible region and start monitoring.
  - Use `change-watch --select-region [name]` to select a region and watch for changes instead of stability.
  - Negative coordinates are valid when a connected display is to the left of or above the main display; do not replace them with zero manually.
  - The monitor checks for off-screen regions on macOS when display information is available. Screenshot failures exit with status 1 and recovery instructions in both monitoring modes.

- **`NotOpenSSLWarning` / an existing LibreSSL environment:**
  - Run `task-watch --update`, then run `task-watch` again. An update started by an older launcher can finish using its already-loaded setup functions; the next launch uses the new environment checks.
  - The launcher checks the existing environment's Python version and SSL backend. It reuses compatible environments and replaces incompatible ones using an OpenSSL-based Python found on `PATH`, in Homebrew's standard directories, or in python.org's framework directory. Finder shortcuts use the same setup.
  - If no compatible interpreter is installed, setup stops with installation instructions. Install Python as described in the prerequisites, then retry.
  - To choose the interpreter for a new or replacement environment, use `TASK_WATCH_PYTHON=/absolute/path/to/python3 task-watch`. This setting does not replace an already compatible environment.
  - Replacement preserves the old environment under `python/.venv-backup-<id>`. Failed environment creation or package installation restores the original environment. Keep the backup until the new environment works; a backup must be moved back to `python/.venv` before being used directly because virtual environments contain absolute paths.
  - Saved regions and notification settings stay in `config/config.txt`, outside the environment. Setup and updates upgrade pip inside the virtual environment. Requirements are installed through that environment's Python without forcing dependency upgrades.
  - This fixes the SSL backend; urllib3 warnings are not filtered and urllib3 is not downgraded. See the [urllib3 migration guide](https://urllib3.readthedocs.io/en/stable/v2-migration-guide.html) for supported TLS libraries.

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

## Local validation

With the requirements installed, run from the repository root:

```bash
PYTHONPATH=python python -m unittest discover -s python/tests -v
```

These tests mock the display and capture boundaries and disable notification transports.
They do not capture your desktop or send notifications.

Capture and environment diagnostics use Python's standard `gettext` provider with English and German catalogs under
`python/task_completion_detector/locales/`. Other existing CLI messages retain their current language.
Locale selection follows `LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, and `LANG`, with English as the fallback.
After editing a catalog, regenerate its compiled file using GNU gettext, for example:

```bash
msgfmt --check --check-format -o python/task_completion_detector/locales/en/LC_MESSAGES/messages.mo python/task_completion_detector/locales/en/LC_MESSAGES/messages.po
msgfmt --check --check-format -o python/task_completion_detector/locales/de/LC_MESSAGES/messages.mo python/task_completion_detector/locales/de/LC_MESSAGES/messages.po
```
