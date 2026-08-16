#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:-}"

if [[ -z "${IMAGE_REF}" ]]; then
  echo "Usage: $0 <registry-image@digest>" >&2
  exit 2
fi

command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required" >&2; exit 127; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required" >&2; exit 127; }

echo "Verifying BuildKit attestations for ${IMAGE_REF}"

SBOM_JSON="$(docker buildx imagetools inspect "${IMAGE_REF}" --format '{{json .SBOM}}')"
PROVENANCE_JSON="$(docker buildx imagetools inspect "${IMAGE_REF}" --format '{{json .Provenance}}')"

if [[ -z "${SBOM_JSON}" || "${SBOM_JSON}" == "null" ]]; then
  echo "ERROR: no SBOM attestation found" >&2
  exit 1
fi

if ! printf '%s' "${SBOM_JSON}" | jq -e 'any(.. | objects; has("SPDXID"))' >/dev/null; then
  echo "ERROR: SBOM data is present but no SPDX document was found" >&2
  exit 1
fi

echo "Verified SBOM attestation: present (SPDX)"

if [[ -z "${PROVENANCE_JSON}" || "${PROVENANCE_JSON}" == "null" ]]; then
  echo "ERROR: no provenance attestation found" >&2
  exit 1
fi

# Buildx exposes SLSA provenance through .Provenance.SLSA. SLSA v1 uses
# buildDefinition/runDetails, whereas SLSA v0.2 uses builder/invocation/etc.
if ! printf '%s' "${PROVENANCE_JSON}" | jq -e '.SLSA | type == "object" and has("buildDefinition") and has("runDetails")' >/dev/null; then
  echo "ERROR: SLSA v1 provenance attestation not found" >&2
  exit 1
fi

echo "Verified SLSA provenance attestation: present (v1)"
