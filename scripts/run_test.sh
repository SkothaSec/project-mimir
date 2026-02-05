#!/bin/bash
set -euo pipefail

# Ensure gcloud SDK is on PATH for non-interactive shells.
if [[ -f "/Users/skwl/Documents/repos/google-cloud-sdk/path.bash.inc" ]]; then
  # shellcheck source=/Users/skwl/Documents/repos/google-cloud-sdk/path.bash.inc
  . "/Users/skwl/Documents/repos/google-cloud-sdk/path.bash.inc"
fi

# Default to "anchoring" "trap" if no args provided
TEST_TYPE=${1:-anchoring}
VARIANT=${2:-trap}

# Resolve project ID: env override, then gcloud config.
PROJECT_ID="${PROJECT_ID:-}"
if [[ -z "${PROJECT_ID}" ]]; then
  PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
fi

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "ERROR: Set PROJECT_ID env var or 'gcloud config set project <id>'" >&2
  exit 1
fi

# Ensure local venv with deps
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
REQ_FILE="${ROOT_DIR}/requirements.txt"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

if [[ -f "${REQ_FILE}" ]]; then
  pip install --quiet --upgrade pip
  pip install --quiet -r "${REQ_FILE}"
fi

echo "Generating $TEST_TYPE ($VARIANT) for Project: $PROJECT_ID..."

# Run the python script with the --send flag using venv python
python "${ROOT_DIR}/src/mimir_generator.py" "$TEST_TYPE" --variant "$VARIANT" --project "$PROJECT_ID" --send

echo "Done. Check BigQuery in ~30 seconds."
