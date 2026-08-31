#!/usr/bin/env bash
set -euo pipefail

GRYPE="${GRYPE:-grype}"

if ! command -v "${GRYPE}" >/dev/null 2>&1 && [[ ! -x "${GRYPE}" ]]; then
    echo "ERROR: Grype executable not found: ${GRYPE}" >&2
    exit 127
fi

echo "Using Grype: ${GRYPE}"
"${GRYPE}" version

echo "Updating Grype vulnerability database..."
"${GRYPE}" db update

echo "Checking Grype vulnerability database..."
"${GRYPE}" db status
