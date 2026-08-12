#!/usr/bin/env bash

set -euo pipefail

IMAGE="${1:-}"
TAG="${2:-${TAG:-local}}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${REPORT_DIR:-${ROOT}/reports}"
REPORT="${REPORT_DIR}/${IMAGE}-${TAG}-grype.json"

GRYPE="${GRYPE:-grype}"

if [[ -z "${IMAGE}" ]]; then
    echo "Usage: $0 <image> [tag]" >&2
    exit 2
fi

if ! command -v "${GRYPE}" >/dev/null 2>&1 && [[ ! -x "${GRYPE}" ]]; then
    echo "ERROR: Grype executable not found: ${GRYPE}" >&2
    exit 127
fi

mkdir -p "${REPORT_DIR}"

echo "Scanning container-factory/${IMAGE}:${TAG}"
echo "Using Grype: ${GRYPE}"

"${GRYPE}" \
    "container-factory/${IMAGE}:${TAG}" \
    --output json \
    --file "${REPORT}"

echo
echo "Vulnerability report written to ${REPORT}"

"${ROOT}/scripts/security-policy.sh" "${REPORT}"
