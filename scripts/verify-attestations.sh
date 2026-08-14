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
command -v cosign >/dev/null 2>&1 || { echo "ERROR: cosign is required" >&2; exit 127; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required" >&2; exit 127; }

TMP="$(mktemp)"
trap 'rm -f "${TMP}"' EXIT

echo "Verifying attestations for ${IMAGE_REF}"
cosign verify-attestation \
  --certificate-identity "${IDENTITY}" \
  --certificate-oidc-issuer "${ISSUER}" \
  --output json \
  "${IMAGE_REF}" > "${TMP}"

if ! jq -e 'length > 0' "${TMP}" >/dev/null; then
  echo "ERROR: no verified attestations found" >&2
  exit 1
fi

if ! jq -e '[.[] | select(.payload | @base64d | fromjson | .predicateType == "https://spdx.dev/Document")] | length > 0' "${TMP}" >/dev/null; then
  echo "ERROR: verified SPDX SBOM attestation not found" >&2
  exit 1
fi

if ! jq -e '[.[] | select(.payload | @base64d | fromjson | (.predicateType | startswith("https://slsa.dev/provenance/")))] | length > 0' "${TMP}" >/dev/null; then
  echo "ERROR: verified SLSA provenance attestation not found" >&2
  exit 1
fi

echo "Verified SBOM attestation: present"
echo "Verified SLSA provenance attestation: present"
