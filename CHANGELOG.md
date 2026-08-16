# Changelog

## 2.2.1

- Update Node.js image to `node:26.7-trixie-slim`.
- Update Go image to `golang:1.26.6-trixie`.
- Move Node.js and Go off Debian Bookworm onto Debian Trixie to avoid the EOL-distro scan warning and reduce stale vulnerability data.
- Update image metadata and security-focused tests accordingly.

## 2.2.0

- Add Node.js 24.18.0 runtime image.
- Add Go 1.26.5 development image.
- Add Nginx 1.30.4 Alpine image running as an unprivileged user on port 8080.
- Add Debian 13 (Trixie) slim base image.
- Add Ubuntu 24.04 LTS base image.
- Extend CI and Release matrices to cover all seven factory images.


- Fix release matrix filtering by removing the invalid job-level `matrix` expression.
- Release now publishes all declared images when triggered, including manual dispatches.
- Fix keyless Cosign verification to trust the reusable workflow that actually receives the OIDC identity.
- Document the reusable workflow as the signing identity.
- Keep CI and Release permissions separated at the caller boundary.

# Changelog

## 2.2.1

- Update Node.js image to `node:26.7-trixie-slim`.
- Update Go image to `golang:1.26.6-trixie`.
- Move Node.js and Go off Debian Bookworm onto Debian Trixie to avoid the EOL-distro scan warning and reduce stale vulnerability data.
- Update image metadata and security-focused tests accordingly.

## 2.1.3

- Add image-scoped, time-limited vulnerability exceptions.
- Pass image identity into security-policy evaluation so exceptions cannot leak between images.
- Report active and expired exceptions explicitly.


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
