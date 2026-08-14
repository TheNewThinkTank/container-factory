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
