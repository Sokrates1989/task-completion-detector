bootstrap_python_env() {
  cd "${PROJECT_ROOT}/python"

  # Choose Python interpreter: prefer macOS /usr/bin/python3 (has Tk) then fall back to python3
  if [ -x /usr/bin/python3 ]; then
    PYTHON_BIN=/usr/bin/python3
  else
    PYTHON_BIN=python3
  fi

  # Create venv if missing
  if [ ! -d .venv ]; then
    echo "Creating virtual environment using ${PYTHON_BIN}..."
    "${PYTHON_BIN}" -m venv .venv
  fi

  # Activate venv
  source .venv/bin/activate

  # Install/update dependencies
  pip install -r ../requirements.txt
}

migrate_screenshot_config() {
  local config_path="${PROJECT_ROOT}/config/config.txt"

  if [ ! -f "${config_path}" ]; then
    return
  fi

  CONFIG_PATH="${config_path}" python << 'PY'
import json
import os
import sys

path = os.environ.get("CONFIG_PATH")
if not path or not os.path.exists(path):
    sys.exit(0)

try:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
except Exception:
    print(f"[WARN] Could not parse config at {path} for migration; skipping screenshot migration.")
    sys.exit(0)

notif = cfg.get("notifications")
if not isinstance(notif, dict):
    sys.exit(0)

if "includeScreenshotInTelegram" in notif:
    sys.exit(0)

print()
print("Your config was created before Telegram screenshot support was added.")

def ask() -> bool:
    """Ask user on the real TTY instead of stdin.

    The script itself is provided via stdin (here-doc), so reading from stdin
    would immediately hit EOF. By opening /dev/tty we can still interact with
    the user when a TTY is available, and safely default to "no" otherwise.
    """
    try:
        tty = open("/dev/tty", "r")
    except OSError:
        # No TTY available (e.g. non-interactive run) -> default to "no"
        return False

    try:
        while True:
            sys.stdout.write("Enable sending screenshots in Telegram notifications? [y/N] ")
            sys.stdout.flush()
            ans = tty.readline()
            if not ans:
                # EOF from TTY -> default to "no"
                return False
            ans = ans.strip().lower()
            if ans in ("", "n", "no"):
                return False
            if ans in ("y", "yes"):
                return True
            print("Please answer y or n.")
    finally:
        tty.close()

enable = ask()
notif["includeScreenshotInTelegram"] = enable

try:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print(f"Config updated: notifications.includeScreenshotInTelegram = {enable}")
except Exception:
    print(f"[WARN] Failed to write updated config to {path}")
PY
}

run_update() {
  if [ ! -d "${PROJECT_ROOT}/.git" ]; then
    echo "No .git directory found at ${PROJECT_ROOT}. Auto-update requires a git clone."
    exit 1
  fi

  echo "Updating task-completion-detector in ${PROJECT_ROOT}..."
  cd "${PROJECT_ROOT}"
  git pull --ff-only || {
    echo "Warning: git pull failed (non-fast-forward or error)."
    exit 1
  }
  echo "Code update complete. Refreshing Python environment..."
  bootstrap_python_env
  echo "Python environment refreshed."

  migrate_screenshot_config

  echo "Update finished."
}

check_for_updates() {
  # Only works for git clones; silently skip otherwise
  if [ ! -d "${PROJECT_ROOT}/.git" ]; then
    return
  fi

  cd "${PROJECT_ROOT}"

  # Quietly update remote tracking information; ignore errors so we don't break the main flow
  git remote update >/dev/null 2>&1 || return

  local local_hash remote_hash base_hash
  local_hash=$(git rev-parse @ 2>/dev/null) || return
  remote_hash=$(git rev-parse @{u} 2>/dev/null) || return
  base_hash=$(git merge-base @ @{u} 2>/dev/null) || return

  # Remote is ahead of local (fast-forward available): notify user once
  if [ "${local_hash}" = "${base_hash}" ] && [ "${remote_hash}" != "${local_hash}" ]; then
    echo "[Update available] A newer version of task-completion-detector is available. Run 'task-watch --update' to update."
  fi
}
