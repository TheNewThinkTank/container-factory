#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:-}"

if [[ -z "${IMAGE_REF}" ]]; then
  echo "Usage: $0 <registry-image@digest>" >&2
  exit 2
fi

command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required" >&2; exit 127; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required" >&2; exit 127; }

RAW="$(docker buildx imagetools inspect --raw "${IMAGE_REF}")"
MEDIA_TYPE="$(printf '%s' "${RAW}" | jq -r '.mediaType // empty')"

if [[ "${MEDIA_TYPE}" != "application/vnd.oci.image.index.v1+json" && \
      "${MEDIA_TYPE}" != "application/vnd.docker.distribution.manifest.list.v2+json" ]]; then
  echo "ERROR: ${IMAGE_REF} is not a multi-platform image index (mediaType=${MEDIA_TYPE:-unknown})" >&2
  exit 1
fi

count="$(printf '%s' "${RAW}" | jq '[.manifests[]? | select(.platform.os == "linux" and (.platform.architecture == "amd64" or .platform.architecture == "arm64"))] | length')"
amd64="$(printf '%s' "${RAW}" | jq '[.manifests[]? | select(.platform.os == "linux" and .platform.architecture == "amd64")] | length')"
arm64="$(printf '%s' "${RAW}" | jq '[.manifests[]? | select(.platform.os == "linux" and .platform.architecture == "arm64")] | length')"

if [[ "${amd64}" -ne 1 || "${arm64}" -ne 1 ]]; then
  echo "ERROR: expected exactly one linux/amd64 and one linux/arm64 image manifest; found amd64=${amd64}, arm64=${arm64}" >&2
  exit 1
fi

echo "Valid multi-platform image index: ${IMAGE_REF}"
echo "  linux/amd64: present"
echo "  linux/arm64: present"
echo "  platform image manifests: ${count}"
