#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:-}"

if [[ -z "${IMAGE_REF}" ]]; then
  echo "Usage: $0 <image-ref>" >&2
  exit 2
fi

command -v docker >/dev/null 2>&1 || {
  echo "ERROR: docker is required" >&2
  exit 127
}

docker buildx imagetools inspect "${IMAGE_REF}"
