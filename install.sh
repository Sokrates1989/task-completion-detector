#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCHER_DIR="${SCRIPT_DIR}/launchers"

mkdir -p "${LAUNCHER_DIR}"

# Ensure launchers are executable
chmod +x "${LAUNCHER_DIR}/ai-select.sh" "${LAUNCHER_DIR}/ai-watch.sh" \
  "${LAUNCHER_DIR}/ai-select.command" "${LAUNCHER_DIR}/ai-watch.command"

# Create symlinks in /usr/local/bin for terminal use, if possible
BIN_DIR="/usr/local/bin"
if [ -w "${BIN_DIR}" ]; then
  ln -sf "${LAUNCHER_DIR}/ai-select.sh" "${BIN_DIR}/ai-select"
  ln -sf "${LAUNCHER_DIR}/ai-watch.sh" "${BIN_DIR}/ai-watch"
  echo "Created symlinks ai-select and ai-watch in ${BIN_DIR}."
else
  echo "Warning: cannot write to ${BIN_DIR}. Run this script with sudo if you want global commands ai-select/ai-watch."
fi

########## Desktop shortcuts ##########
# Create double-clickable .command wrappers on Desktop that call the launchers
DESKTOP_DIR="${HOME}/Desktop"

cat > "${DESKTOP_DIR}/ai-select.command" <<EOF
#!/bin/zsh
"${LAUNCHER_DIR}/ai-select.sh"
EOF

cat > "${DESKTOP_DIR}/ai-watch.command" <<EOF
#!/bin/zsh
"${LAUNCHER_DIR}/ai-watch.sh"
EOF

chmod +x "${DESKTOP_DIR}/ai-select.command" "${DESKTOP_DIR}/ai-watch.command"

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
echo "- From terminal: run 'ai-select' or 'ai-watch' (if /usr/local/bin symlinks succeeded)."
echo "- From Finder: double-click ai-select.command or ai-watch.command on your Desktop."

if [[ "${OSTYPE}" == darwin* ]]; then
  echo
  echo "macOS note:"
  echo "- The first time you run 'ai-select' or 'ai-watch', macOS will ask for Screen Recording permission."
  echo "- This tool needs Screen Recording so it can capture small screenshots of the selected region and compare"
  echo "  them over time to detect when your AI assistant has stopped changing the UI (task finished / needs input)."
fi
