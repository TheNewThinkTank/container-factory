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

INSPECT_JSON="$(docker buildx imagetools inspect "${IMAGE_REF}" --format '{{json .}}')"

SBOM_JSON="$(printf '%s' "${INSPECT_JSON}" | jq -c '.SBOM // null')"
PROVENANCE_JSON="$(printf '%s' "${INSPECT_JSON}" | jq -c '.Provenance // null')"

if [[ -z "${SBOM_JSON}" || "${SBOM_JSON}" == "null" ]]; then
  echo "ERROR: no SBOM attestation found" >&2
  exit 1
fi

# For a multi-platform image, Buildx exposes SBOM data by platform.
# Require an SPDX document for both image platforms we publish.
for platform in linux/amd64 linux/arm64; do
  platform_sbom="$(printf '%s' "${SBOM_JSON}" | jq -c --arg p "${platform}" '.[$p] // null')"

  if [[ -z "${platform_sbom}" || "${platform_sbom}" == "null" ]]; then
    echo "ERROR: SBOM attestation not found for ${platform}" >&2
    exit 1
  fi

  if ! printf '%s' "${platform_sbom}" | jq -e '(.SPDX // null) | type == "object" and has("SPDXID")' >/dev/null; then
    echo "ERROR: SBOM attestation for ${platform} is not a valid SPDX document" >&2
    exit 1
  fi

  echo "Verified SBOM attestation: ${platform} (SPDX)"
done

if [[ -z "${PROVENANCE_JSON}" || "${PROVENANCE_JSON}" == "null" ]]; then
  echo "ERROR: no provenance attestation found" >&2
  exit 1
fi

# Buildx exposes multi-platform provenance as a map keyed by platform.
# For SLSA Provenance v1, each platform's SLSA predicate contains
# buildDefinition and runDetails. This is different from SLSA v0.2,
# which used builder/invocation/metadata at the top level.
for platform in linux/amd64 linux/arm64; do
  platform_provenance="$(printf '%s' "${PROVENANCE_JSON}" | jq -c --arg p "${platform}" '.[$p] // null')"

  if [[ -z "${platform_provenance}" || "${platform_provenance}" == "null" ]]; then
    echo "ERROR: SLSA provenance attestation not found for ${platform}" >&2
    exit 1
  fi

  if ! printf '%s' "${platform_provenance}" | jq -e '.SLSA | type == "object" and has("buildDefinition") and has("runDetails")' >/dev/null; then
    echo "ERROR: SLSA v1 provenance attestation not found for ${platform}" >&2
    exit 1
  fi

  echo "Verified SLSA provenance attestation: ${platform} (v1)"
done
