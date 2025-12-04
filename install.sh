#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCHER_DIR="${SCRIPT_DIR}/launchers"
TASK_WATCH_SCRIPT="${SCRIPT_DIR}/task-watch.sh"

mkdir -p "${LAUNCHER_DIR}"

# Ensure main entrypoint is executable
chmod +x "${TASK_WATCH_SCRIPT}"

# Create symlinks in /usr/local/bin for terminal use, if possible
BIN_DIR="/usr/local/bin"
if [ -w "${BIN_DIR}" ]; then
  ln -sf "${TASK_WATCH_SCRIPT}" "${BIN_DIR}/task-watch"
  ln -sf "${TASK_WATCH_SCRIPT}" "${BIN_DIR}/ai-select"
  ln -sf "${TASK_WATCH_SCRIPT}" "${BIN_DIR}/ai-watch"
  echo "Created symlinks task-watch, ai-select and ai-watch in ${BIN_DIR}."
else
  echo "Warning: cannot write to ${BIN_DIR}. Run this script with sudo if you want global commands task-watch / ai-select / ai-watch."
fi

########## Desktop shortcuts ##########
# Create double-clickable .command wrappers on Desktop that call the main entrypoint
DESKTOP_DIR="${HOME}/Desktop"

cat > "${DESKTOP_DIR}/task-watch.command" <<EOF
#!/bin/zsh
"${TASK_WATCH_SCRIPT}" "$@"
EOF

cat > "${DESKTOP_DIR}/ai-select.command" <<EOF
#!/bin/zsh
"${TASK_WATCH_SCRIPT}" --select-region "$@"
EOF

cat > "${DESKTOP_DIR}/ai-watch.command" <<EOF
#!/bin/zsh
"${TASK_WATCH_SCRIPT}" "$@"
EOF

chmod +x "${DESKTOP_DIR}/task-watch.command" "${DESKTOP_DIR}/ai-select.command" "${DESKTOP_DIR}/ai-watch.command"

########## Config setup guidance (guided Python wizard) ##########
PYTHON_SETUP_DIR="${SCRIPT_DIR}/python"
cd "${PYTHON_SETUP_DIR}"

if [ -x /usr/bin/python3 ]; then
  PYTHON_BIN=/usr/bin/python3
else
  PYTHON_BIN=python3
fi

if [ ! -d .venv ]; then
  echo "Creating virtual environment for setup using ${PYTHON_BIN}..."
  "${PYTHON_BIN}" -m venv .venv
fi

source .venv/bin/activate
pip install -r ../requirements.txt

echo "Starting guided configuration setup..."
python main.py setup-config

cd "${SCRIPT_DIR}"

########## Fix config ownership when run with sudo ##########
if [ -n "${SUDO_USER}" ]; then
  TARGET_USER="${SUDO_USER}"
  TARGET_GROUP="$(id -gn "${SUDO_USER}" 2>/dev/null || echo "${SUDO_USER}")"
  chown -R "${TARGET_USER}:${TARGET_GROUP}" "${SCRIPT_DIR}/config" 2>/dev/null || {
    echo "Warning: could not adjust ownership of ${SCRIPT_DIR}/config."
    echo "To fix manually, run this from your normal user account:"
    echo "  sudo chown -R \"\$USER\":\"\$(id -gn \"\$USER\")\" \"${SCRIPT_DIR}/config\""
  }
fi

echo "Installation complete."
echo "- From terminal: run 'task-watch' as the main entrypoint (if /usr/local/bin symlinks succeeded)."
echo "  * 'task-watch'                → monitor last selected default region."
echo "  * 'task-watch --select-region' → select region and then start monitoring."
echo "  * 'task-watch --config'        → (re)run guided configuration / config editor."
echo "- Backwards-compatible aliases: 'ai-select' and 'ai-watch' still work and forward to task-watch."
echo "- From Finder: double-click task-watch.command, ai-select.command or ai-watch.command on your Desktop."

if [[ "${OSTYPE}" == darwin* ]]; then
  echo
  echo "macOS note:"
  echo "- The first time you run 'task-watch' (or 'ai-select' / 'ai-watch'), macOS will ask for Screen Recording permission."
  echo "- This tool needs Screen Recording so it can capture small screenshots of the selected region and compare"
  echo "  them over time to detect when your AI assistant has stopped changing the UI (task finished / needs input)."
fi
