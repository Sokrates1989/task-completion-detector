#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCHER_DIR="${SCRIPT_DIR}/launchers"
TASK_WATCH_SCRIPT="${SCRIPT_DIR}/task-watch.sh"

mkdir -p "${LAUNCHER_DIR}"

# Ensure main entrypoint is executable
chmod +x "${TASK_WATCH_SCRIPT}"

# Create symlinks in /usr/local/bin for terminal use
BIN_DIR="/usr/local/bin"
if [ -w "${BIN_DIR}" ]; then
  ln -sf "${TASK_WATCH_SCRIPT}" "${BIN_DIR}/task-watch"
  # Legacy aliases (silent, for backward compatibility)
  ln -sf "${TASK_WATCH_SCRIPT}" "${BIN_DIR}/ai-select"
  ln -sf "${TASK_WATCH_SCRIPT}" "${BIN_DIR}/ai-watch"
  echo "Created 'task-watch' command in ${BIN_DIR}."
else
  echo "Warning: cannot write to ${BIN_DIR}. Run this script with sudo to enable the 'task-watch' command."
fi

########## Desktop shortcuts ##########
# Create double-clickable .command wrapper on Desktop
# Use real user's home when running with sudo
if [ -n "${SUDO_USER}" ]; then
  REAL_HOME=$(eval echo "~${SUDO_USER}")
else
  REAL_HOME="${HOME}"
fi
DESKTOP_DIR="${REAL_HOME}/Desktop"

cat > "${DESKTOP_DIR}/task-watch.command" <<EOF
#!/bin/zsh
"${TASK_WATCH_SCRIPT}" "\$@"
EOF

chmod +x "${DESKTOP_DIR}/task-watch.command"

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
echo "- From terminal: run 'task-watch' as the main entrypoint."
echo "  * 'task-watch'                 → monitor last selected default region."
echo "  * 'task-watch --select-region' → select region and then start monitoring."
echo "  * 'task-watch --config'        → (re)run guided configuration / config editor."
echo "  * 'task-watch --update'        → update to latest version."
echo "- From Finder: double-click task-watch.command on your Desktop."

if [[ "${OSTYPE}" == darwin* ]]; then
  echo
  echo "macOS note:"
  echo "- The first time you run 'task-watch', macOS will ask for Screen Recording permission."
  echo "- This tool needs Screen Recording so it can capture small screenshots of the selected region and compare"
  echo "  them over time to detect when your AI assistant has stopped changing the UI (task finished / needs input)."
fi
