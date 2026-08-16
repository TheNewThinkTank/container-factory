[![CI](https://github.com/TheNewThinkTank/container-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/TheNewThinkTank/container-factory/actions/workflows/ci.yml)
[![Release container images](https://github.com/TheNewThinkTank/container-factory/actions/workflows/release.yml/badge.svg)](https://github.com/TheNewThinkTank/container-factory/actions/workflows/release.yml)

# container-factory

A small, opinionated container-image factory for building, testing, scanning,
attesting, signing, and publishing multi-architecture container images.


> **v2.2.0:** The reusable workflow intentionally declares no elevated `GITHUB_TOKEN` permissions. Callers grant only the permissions they need: CI is read-only; Release grants package publishing and OIDC signing.

## v2 supply-chain model

v2 makes the immutable image digest the identity of a release. The release
workflow:

1. validates image metadata;
2. builds and pushes `linux/amd64` and `linux/arm64` with Docker Buildx;
3. attaches an SBOM attestation;
4. attaches max-level BuildKit provenance;
5. validates that the Buildx digest identifies a real multi-platform image
   index containing `linux/amd64` and `linux/arm64`;
6. records the resulting immutable image-index digest;
7. scans the exact platform manifests behind that digest with Grype;
8. evaluates the factory security policy;
9. signs the exact multi-architecture digest with Sigstore/Cosign using GitHub
   Actions OIDC;
10. verifies the signature; and
11. verifies that both the SBOM and SLSA provenance attestations are attached
    to and cryptographically verified for that same digest.

Docker Buildx supports SBOM and provenance attestations directly through
`docker/build-push-action`; provenance is generated as an in-toto attestation
and attached to the final image.

Cosign keyless signing binds an ephemeral signing key to the GitHub Actions
OIDC identity and records the signing event in Sigstore's transparency log.
citeturn0search1turn0search2

## Repository layout

```text
container-factory/
├── images/
├── scripts/
│   ├── build-image.sh
│   ├── generate-sbom.sh
│   ├── inspect-image-digest.sh
│   ├── prepare-grype.sh
│   ├── promote-image.sh
│   ├── scan-image.sh
│   ├── scan-multiarch-image.sh
│   ├── security-policy.sh
│   ├── setup-security-tools.sh
│   ├── sign-image.sh
│   ├── validate-metadata.py
│   └── verify-image.sh
├── src/container_factory/
├── tests/
├── .config/security-policy.yaml
└── .github/workflows/
    ├── ci.yml
    ├── release.yml
    └── reusable-container.yml
```

## Image catalog

The factory currently publishes seven reference images:

| Image | Upstream base | Purpose |
|---|---|---|
| `hello` | Alpine 3.24 | Minimal smoke-test image |
| `python` | Python 3.14.7 / Debian Trixie slim | Python runtime |
| `node` | Node.js 26.7 / Debian Trixie slim | JavaScript/TypeScript runtime |
| `go` | Go 1.26.6 / Debian Trixie | Go development runtime |
| `nginx` | Nginx 1.30.4 / Alpine 3.24 | Web server running unprivileged on port 8080 |
| `debian` | Debian Trixie slim | General-purpose Linux base |
| `ubuntu` | Ubuntu 24.04 (metadata version 24.4.0) | General-purpose Linux base |

The Node.js, Go, Nginx, Debian, and Ubuntu definitions are reference images for demonstrating the same factory controls across runtime and operating-system ecosystems.

## Immutable image identity

Tags are human-friendly pointers. They are not the security identity of an
artifact. v2 uses:

```text
ghcr.io/<owner>/<image>@sha256:<digest>
```

The digest returned by the Buildx release step is the digest used for security
scanning, signing, and verification.

## Attestations

The release build uses:

```text
provenance: mode=max,version=v1
sbom: true
```

BuildKit attaches these attestations to the pushed image. OCI registries may
represent these attachments as separate referrer artifacts. Those referrer
digests are deliberately not confused with the digest of the image index itself.

## Signing

The release workflow uses keyless Cosign signing. No long-lived private key is
stored in GitHub secrets. The workflow requires:

```yaml
permissions:
  packages: write
  id-token: write
```

Cosign signs the immutable digest, not a mutable tag. Verification is restricted
to the release workflow identity for this repository on `main`.

For local verification after a release, install Cosign and run:

```bash
export COSIGN_CERTIFICATE_IDENTITY='https://github.com/TheNewThinkTank/container-factory/.github/workflows/reusable-container.yml@refs/heads/main'
make verify IMAGE=python DIGEST=sha256:<digest>
```

Sigstore documents keyless container signing and verification with Cosign.
citeturn0search1turn0search3

## Security policy

Grype discovers vulnerabilities; the factory's Python policy engine decides
whether they block publication. The default policy is:

```yaml
security:
  fail_severity:
    - critical
    - high
  high_cvss_threshold: 7.0
  no_fix_action: review
  ignore_severity:
    - medium
    - low
    - negligible
    - unknown
  images:
    python:
      vulnerability_exceptions:
        - id: CVE-2026-15308
          reason: >
            CVE affects CPython html.parser.HTMLParser.
            The published runtime image does not itself process
            attacker-controlled HTML. Downstream applications
            remain responsible for assessing exposure.
          expires: 2026-09-30
```

The release scan is performed against the exact child manifests for the
supported Linux architectures rather than against a separately rebuilt image.

Vulnerability exceptions are scoped to an individual image and expire on a
specific date. An exception suppresses only the matching CVE for that image;
expired exceptions fail the policy gate.

## Local usage

Requirements:

- Docker + Buildx
- Bash
- Python 3.11+
- PyYAML
- Syft
- Grype
- Cosign for signing/verification

```bash
make setup
make validate
make test
make build IMAGE=hello
make sbom IMAGE=hello
make scan IMAGE=hello
```

Inspect a registry image:

```bash
make inspect REGISTRY_IMAGE=ghcr.io/thenewthinktank/python
```

Verify a released digest:

```bash
export COSIGN_CERTIFICATE_IDENTITY='https://github.com/TheNewThinkTank/container-factory/.github/workflows/reusable-container.yml@refs/heads/main'
make verify IMAGE=python DIGEST=sha256:<digest>
```

## GitHub setup

The release workflow publishes to GHCR using `GITHUB_TOKEN`. It also needs
GitHub's OIDC token permission for keyless signing:

```yaml
permissions:
  contents: read
  packages: write
  id-token: write
```

No Cosign private key or registry password is required.

## CI and release workflows

CI and Release intentionally remain separate entry points. CI answers “is this change safe to merge?” and builds/scans local `linux/amd64` images without publishing or signing. Release answers “is this exact artifact safe to distribute?” and performs the multi-platform build, attestations, digest-based security gate, signing, and verification.

The implementation is shared through `.github/workflows/reusable-container.yml`, so build and security logic is defined once rather than duplicated between CI and Release. GitHub reusable workflows support typed `workflow_call` inputs and can be invoked from matrix jobs.

CI is deliberately granted only `contents: read`. Release grants `packages: write` and `id-token: write` because it publishes to GHCR and performs keyless signing.

## v2 scope

v2 deliberately focuses on four supply-chain primitives:

- immutable OCI digests;
- SBOM attestations;
- SLSA/in-toto-style BuildKit provenance;
- keyless Sigstore/Cosign signatures and verification.

Admission control, policy engines, registry promotion, and consumer-side
verification beyond signature identity are intentionally left for later
versions.


## Attestation model

Release builds publish BuildKit SBOM and SLSA Provenance v1 attestations alongside the image index. The release gate inspects the published registry artifact with `docker buildx imagetools inspect` and requires SPDX SBOM data and the SLSA v1 `buildDefinition`/`runDetails` structure. Cosign signature verification is performed separately against the immutable image digest. BuildKit attestations and Cosign signatures are deliberately treated as different supply-chain artifacts.
