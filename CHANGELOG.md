# Changelog

## 2.0.0 — 2026-08-14

### Added

- Immutable OCI digest as the release artifact identity.
- Multi-architecture Buildx release build using `linux/amd64` and `linux/arm64`.
- BuildKit SBOM attestations.
- Max-level BuildKit provenance attestations.
- Exact-digest multi-architecture vulnerability scanning.
- Keyless Sigstore/Cosign signing using GitHub Actions OIDC.
- Signature verification bound to the release workflow identity.
- Scripts for digest inspection, signing, verification and multi-architecture scanning.
- Local Makefile targets for image inspection, signing and verification.
- CI shell-script syntax validation.

### Changed

- Release workflow now uses `docker/build-push-action@v7`.
- Release workflow requests `id-token: write` for keyless signing.
- Security scanning happens against the exact published digest.
- Manual releases are restricted to the `main` branch so the verification identity is stable.

## 1.1.0 — 2026-08-14

- Hardened metadata validation.
- Added explicit Grype database preparation.
- Expanded policy tests.
- Fixed manual release selection.

## 2.0.1 — 2026-08-14

### Fixed

- Added an explicit assertion that the Buildx output digest is a real multi-platform image index containing exactly linux/amd64 and linux/arm64 image manifests.
- Added post-release verification for both SBOM and SLSA provenance attestations.
- Made multi-platform scanning fail closed when given an attestation-only OCI artifact/referrer instead of an image index.
- Clarified that GHCR may expose BuildKit attestations as OCI referrer artifacts whose digest/tag is not the image digest; the factory always uses the Buildx image-index digest as the artifact identity.
