# Installation & configuration

## Prerequisites

- macOS (tested) with Python 3.9+
- Git
- Optional: Telegram account (for Telegram notifications)
- Optional: SMTP email account (for email notifications)

---

## Option 1: Quick install on macOS (recommended)

If you want the default setup with Desktop shortcuts and global `ai-select` / `ai-watch` commands, run:

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
  - Creates `ai-select` and `ai-watch` launchers and, if possible, symlinks them into `/usr/local/bin`.
  - Creates double-clickable `ai-select.command` / `ai-watch.command` files on your Desktop.
  - Creates a Python virtual environment under `python/.venv` and installs the required packages.
  - Starts a guided configuration wizard to set up monitoring defaults and notification channels.
  - Fixes ownership of the `config` directory when run with `sudo` so your normal user can edit it.

After this finishes you should be able to:

- From Terminal: run `ai-select` or `ai-watch`.
- From Finder: double-click `ai-select.command` or `ai-watch.command` on your Desktop.

> macOS will ask for *Screen Recording* permission the first time you capture the screen. Grant it so the tool can watch your AI window.

---

## Option 2: Manual install

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

---

## Troubleshooting

- **Cannot create `/usr/local/bin` symlinks:**
  - Run `./install.sh` with `sudo` if you want global `ai-select` / `ai-watch` commands.
  - The script will attempt to fix the ownership of the `config` directory back to your normal user.

- **No macOS notification appears:**
  - Notifications are sent via the built-in `osascript display notification` mechanism.
  - Check System Settings → Notifications, locate your terminal app (or iTerm), and allow alerts/banners.

- **Screen Recording permission denied:**
  - Go to System Settings → Privacy & Security → Screen Recording.
  - Enable access for your terminal app (or whichever app you used to run `ai-select` / `ai-watch`).

For more details on how the tool behaves at runtime, see `docs/USAGE.md`.
