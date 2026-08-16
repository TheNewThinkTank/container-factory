#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:-}"
IMAGE_NAME="${2:-}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${REPORT_DIR:-${ROOT}/reports}"
GRYPE="${GRYPE:-grype}"
SECURITY_PYTHON="${SECURITY_PYTHON:-python3}"

if [[ -z "${IMAGE_REF}" ]]; then
  echo "Usage: $0 <registry-image@digest> [image-name]" >&2
  exit 2
fi

command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required" >&2; exit 127; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required" >&2; exit 127; }
command -v "${GRYPE}" >/dev/null 2>&1 || [[ -x "${GRYPE}" ]] || {
  echo "ERROR: Grype executable not found: ${GRYPE}" >&2
  exit 127
}

mkdir -p "${REPORT_DIR}"

"${ROOT}/scripts/assert-image-index.sh" "${IMAGE_REF}"

RAW="$(docker buildx imagetools inspect --raw "${IMAGE_REF}")"
MANIFESTS="$(printf '%s' "${RAW}" | jq -r '
  if .manifests then
    .manifests[]
    | select(.platform.os == "linux")
    | select(.platform.architecture == "amd64" or .platform.architecture == "arm64")
    | [.platform.os, .platform.architecture, .digest] | @tsv
  else
    empty
  end
')"

if [[ -z "${MANIFESTS}" ]]; then
  echo "ERROR: Could not find linux/amd64 or linux/arm64 manifests in ${IMAGE_REF}" >&2
  exit 1
fi

failed=0
while IFS=$'\t' read -r os arch digest; do
  platform="${os}/${arch}"
  echo ""
  echo "Scanning ${platform} manifest ${digest}"

  child_ref="${IMAGE_REF%@*}@${digest}"
  report="${REPORT_DIR}/registry-${arch}-grype.json"
  if ! "${GRYPE}" "${child_ref}" --output json --file "${report}"; then
    echo "ERROR: Grype failed for ${platform}" >&2
    failed=1
    continue
  fi

  if ! "${ROOT}/scripts/security-policy.sh" "${report}" "${IMAGE_NAME}"; then
    failed=1
  fi
done <<< "${MANIFESTS}"

exit "${failed}"
