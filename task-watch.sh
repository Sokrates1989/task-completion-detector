#!/bin/zsh
set -e

# Determine project root based on this script's real location, but keep original name for alias detection
INVOKED_NAME="$(basename "$0")"
SCRIPT_PATH="${0:A}"
SCRIPT_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"

DEFAULT_REGION_NAME="default"
MODE="watch"
REGION_NAME=""

# Backwards-compatible behaviour based on invoked name
if [[ "${INVOKED_NAME}" == "ai-select" ]]; then
  MODE="select"
fi

usage() {
  cat <<EOF
Usage: task-watch [OPTION] [REGION_NAME]

  (no option)            Monitor the last selected default region (${DEFAULT_REGION_NAME}).
  REGION_NAME            Monitor the named region.
  --select-region
  --select
  -r
  -s                     Select a region and then start monitoring it.
  --config
  --setup-config
  --edit-config
  -c                     Run the guided configuration / config editor.
  --update
  -u                     Update the task-completion-detector git clone (if available) and exit.
  --help
  -h                     Show this help.

Notes:
- The default region name is "${DEFAULT_REGION_NAME}". The first selection run stores it there.
- Legacy aliases:
  - Running via the name "ai-select" behaves like: task-watch --select-region
  - Running via the name "ai-watch" behaves like: task-watch
EOF
}

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
  echo "Python environment refreshed. Update finished."
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --select-region|--select|-r|-s)
      MODE="select"
      shift
      ;;
    --config|--setup-config|--edit-config|-c)
      MODE="config"
      shift
      ;;
    --update|-u)
      MODE="update"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      if [[ -z "${REGION_NAME}" ]]; then
        REGION_NAME="$1"
        shift
      else
        echo "Unexpected argument: $1" >&2
        echo
        usage
        exit 1
      fi
      ;;
  esac
done

case "${MODE}" in
  update)
    run_update
    ;;

  select)
    bootstrap_python_env
    if [[ -n "${REGION_NAME}" ]]; then
      python main.py select-region --name "${REGION_NAME}" --also-name "${DEFAULT_REGION_NAME}" && \
        python main.py monitor --name "${REGION_NAME}"
    else
      python main.py select-region --name "${DEFAULT_REGION_NAME}" && \
        python main.py monitor --name "${DEFAULT_REGION_NAME}"
    fi
    ;;

  config)
    bootstrap_python_env
    python main.py setup-config
    ;;

  watch)
    bootstrap_python_env
    if [[ -n "${REGION_NAME}" ]]; then
      python main.py monitor --name "${REGION_NAME}"
    else
      python main.py monitor --name "${DEFAULT_REGION_NAME}"
    fi
    ;;

  *)
    echo "Internal error: unknown MODE='${MODE}'" >&2
    exit 1
    ;;
esac

