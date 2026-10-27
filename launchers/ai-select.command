#!/bin/zsh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Reuse environment setup while preserving this shortcut's selection-only mode.
source "${PROJECT_ROOT}/setup/modules/task-watch-helpers.sh"
bootstrap_python_env

# Run region selection for default region name
python main.py select-region --name default
