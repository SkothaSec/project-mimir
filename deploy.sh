#!/usr/bin/env bash
# Wrapper to run the actual deploy script.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/scripts/deploy.sh" "$@"
