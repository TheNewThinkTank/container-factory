#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:-}"
TAG="${2:-${TAG:-local}}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${REPORT_DIR:-${ROOT}/reports}"
REPORT="${REPORT_DIR}/${IMAGE}-${TAG}-grype.json"

if [[ -z "${IMAGE}" ]]; then
    echo "Usage: $0 <image> [tag]" >&2
    exit 2
fi

mkdir -p "${REPORT_DIR}"

echo "Scanning container-factory/${IMAGE}:${TAG}"

grype     "container-factory/${IMAGE}:${TAG}"     --output json     --file "${REPORT}"

echo
echo "Vulnerability report written to ${REPORT}"

"${ROOT}/scripts/security-policy.sh" "${REPORT}"
