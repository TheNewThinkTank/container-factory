#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:-}"

if [[ -z "${IMAGE_REF}" ]]; then
  echo "Usage: $0 <registry-image@digest>" >&2
  exit 2
fi

command -v cosign >/dev/null 2>&1 || {
  echo "ERROR: cosign is required" >&2
  exit 127
}

# Keyless signing uses GitHub Actions OIDC. No long-lived private key is stored
# in the repository or GitHub secrets.
echo "Signing ${IMAGE_REF}"
cosign sign --yes "${IMAGE_REF}"
