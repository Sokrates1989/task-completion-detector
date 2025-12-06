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
CHANGE_MODE=false

# Load helper functions (bootstrap_python_env, migrate_screenshot_config, run_update, check_for_updates)
HELPERS_PATH="${PROJECT_ROOT}/setup/modules/task-watch-helpers.sh"
if [ -f "${HELPERS_PATH}" ]; then
  # shellcheck source=/dev/null
  . "${HELPERS_PATH}"
fi

# Backwards-compatible behaviour based on invoked name
if [[ "${INVOKED_NAME}" == "ai-select" ]]; then
  MODE="select"
elif [[ "${INVOKED_NAME}" == "change-watch" ]]; then
  CHANGE_MODE=true
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
  --change
  --watch-change
  -w                     Advanced: watch for changes instead of stability (used by change-watch).
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
  - Running via the name "change-watch" behaves like: task-watch --change
EOF
}

# Helper functions (bootstrap_python_env, migrate_screenshot_config, run_update, check_for_updates)
# are defined in setup/modules/task-watch-helpers.sh and sourced above.

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --select-region|--select|-r|-s)
      MODE="select"
      shift
      ;;
    --change|--watch-change|-w)
      CHANGE_MODE=true
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
    check_for_updates
    bootstrap_python_env
    CHANGE_FLAG=""
    if [[ "${CHANGE_MODE}" == true ]]; then
      CHANGE_FLAG="--change"
    fi
    if [[ -n "${REGION_NAME}" ]]; then
      python main.py select-region --name "${REGION_NAME}" --also-name "${DEFAULT_REGION_NAME}" && \
        python main.py monitor --name "${REGION_NAME}" ${CHANGE_FLAG}
    else
      python main.py select-region --name "${DEFAULT_REGION_NAME}" && \
        python main.py monitor --name "${DEFAULT_REGION_NAME}" ${CHANGE_FLAG}
    fi
    ;;

  config)
    bootstrap_python_env
    python main.py setup-config
    ;;

  watch)
    check_for_updates
    bootstrap_python_env
    CHANGE_FLAG=""
    if [[ "${CHANGE_MODE}" == true ]]; then
      CHANGE_FLAG="--change"
    fi
    if [[ -n "${REGION_NAME}" ]]; then
      python main.py monitor --name "${REGION_NAME}" ${CHANGE_FLAG}
    else
      python main.py monitor --name "${DEFAULT_REGION_NAME}" ${CHANGE_FLAG}
    fi
    ;;

  *)
    echo "Internal error: unknown MODE='${MODE}'" >&2
    exit 1
    ;;
esac

