#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:?IMAGE is required}"
TAG="${TAG:-local}"

command -v syft >/dev/null 2>&1 || {
  echo "syft is required: https://github.com/anchore/syft" >&2
  exit 1
}

mkdir -p sbom
syft "container-factory/${IMAGE}:${TAG}" -o cyclonedx-json="sbom/${IMAGE}-${TAG}.cdx.json"
echo "SBOM written to sbom/${IMAGE}-${TAG}.cdx.json"
