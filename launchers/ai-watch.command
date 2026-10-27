#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Reuse environment setup for the legacy monitoring shortcut.
source "${PROJECT_ROOT}/setup/modules/task-watch-helpers.sh"
bootstrap_python_env

# Monitor default region name
python main.py monitor --name default
