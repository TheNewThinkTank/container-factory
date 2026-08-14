#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:-}"
IDENTITY="${COSIGN_CERTIFICATE_IDENTITY:-}"
ISSUER="${COSIGN_OIDC_ISSUER:-https://token.actions.githubusercontent.com}"

if [[ -z "${IMAGE_REF}" ]]; then
  echo "Usage: $0 <registry-image@digest>" >&2
  exit 2
fi

if [[ -z "${IDENTITY}" ]]; then
  echo "ERROR: COSIGN_CERTIFICATE_IDENTITY is required" >&2
  exit 2
fi

command -v cosign >/dev/null 2>&1 || {
  echo "ERROR: cosign is required" >&2
  exit 127
}

echo "Verifying ${IMAGE_REF}"
cosign verify "${IMAGE_REF}" \
  --certificate-identity "${IDENTITY}" \
  --certificate-oidc-issuer "${ISSUER}"
