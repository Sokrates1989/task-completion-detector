#!/bin/zsh
set -e

# Resolve this script's real path (works even when called via symlink)
SCRIPT_PATH="${0:A}"
SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
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

# Run region selection for default region name; if successful, start monitoring immediately
python main.py select-region --name windsurf_panel && \
  python main.py monitor --name windsurf_panel
