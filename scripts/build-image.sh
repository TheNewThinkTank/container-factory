#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:?IMAGE is required}"
TAG="${TAG:-local}"
PLATFORMS="${PLATFORMS:-linux/amd64}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_DIR="${ROOT}/images/${IMAGE}"

[[ -d "${IMAGE_DIR}" ]] || { echo "Unknown image: ${IMAGE}" >&2; exit 1; }
[[ -f "${IMAGE_DIR}/Dockerfile" ]] || { echo "Missing Dockerfile" >&2; exit 1; }

docker buildx build \
  --platform "${PLATFORMS}" \
  --tag "container-factory/${IMAGE}:${TAG}" \
  --load \
  "${IMAGE_DIR}"
