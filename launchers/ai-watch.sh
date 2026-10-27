#!/bin/zsh
set -e

# Resolve this script's real path (works even when called via symlink)
SCRIPT_PATH="${0:A}"
SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Delegate monitoring to the shared launcher setup.
exec "${PROJECT_ROOT}/task-watch.sh" "$@"
