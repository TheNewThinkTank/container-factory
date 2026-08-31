#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT}/.venv-security"

python3 -m venv "${VENV}"
"${VENV}/bin/pip" install -r "${ROOT}/requirements-dev.txt"

echo "Security tooling environment ready: ${VENV}"
