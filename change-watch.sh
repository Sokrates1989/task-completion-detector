#!/bin/zsh
# Wrapper script for change-watch mode on macOS/Unix
# This script invokes task-watch.sh with the --change flag

SCRIPT_PATH="${0:A}"
SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"

exec "${SCRIPT_DIR}/task-watch.sh" --change "$@"
