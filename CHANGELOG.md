# Changelog

## 2.1.1

- Fix reusable workflow permissions: elevated `packages: write` and `id-token: write` are no longer declared by the called workflow.
- CI now supplies only `contents: read`; Release supplies `packages: write` and `id-token: write`.
- Keeps least-privilege permissions at the caller boundary, as required by GitHub reusable-workflow permission propagation.


## 2.1.0

- Add a reusable container workflow as the single implementation of build and security-gate logic.
- Keep CI and Release as separate entry points with different permissions and responsibilities.
- CI builds/scans local linux/amd64 images without publishing or signing.
- Release reuses the same build/security logic and additionally publishes, attests, signs, and verifies immutable digests.
- Keep elevated GHCR and OIDC permissions scoped to the Release caller.


## 2.0.3

- Fix multi-platform BuildKit provenance verification.
- Verify SBOM attestations separately for linux/amd64 and linux/arm64.
- Verify SLSA Provenance v1 separately for linux/amd64 and linux/arm64.
- Account for the Buildx `imagetools inspect` representation where `.Provenance` and `.SBOM` are keyed by platform.

## 2.0.2

- Verify BuildKit SBOM and provenance through `docker buildx imagetools inspect`.
- Request SLSA Provenance v1 explicitly.
- Separate Cosign signature verification from BuildKit attestation verification.

## 2.0.1

- Add strict multi-platform image-index validation.
- Require linux/amd64 and linux/arm64 manifests before scanning/signing.

## 2.0.0

- Add multi-platform builds.
- Add SBOM and SLSA provenance attestations.
- Add keyless Cosign signing and signature verification.

## 2.0.4

- Fix BuildKit attestation verification to query `.SBOM` and `.Provenance` directly with `docker buildx imagetools inspect --format`, rather than serializing the whole inspect object.
- Keep platform-specific SPDX and SLSA v1 validation fail-closed.
