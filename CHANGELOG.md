# Changelog

## 1.1.0

Hardening release before the v2 supply-chain work.

### Added

- Centralized image metadata validation in `src/container_factory/metadata.py`.
- Validation tests for metadata schema and filesystem constraints.
- Explicit `scripts/prepare-grype.sh` to update and verify the Grype database.
- Additional security-policy tests for CVSS boundaries, fail-closed no-fix mode,
  and exception expiry semantics.

### Changed

- CI and release workflows explicitly prepare the Grype vulnerability database
  before scanning.
- `make validate` validates every image metadata file automatically.
- Release workflow manual dispatch now skips unrelated matrix entries correctly.
- Metadata validation now enforces the documented v1 contract.

### Deliberately deferred to v2

- Digest pinning
- OCI SBOM attestations
- SLSA provenance
- Cosign signing
- Consumer-side signature and provenance verification
