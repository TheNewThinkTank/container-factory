[![CI](https://github.com/TheNewThinkTank/container-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/TheNewThinkTank/container-factory/actions/workflows/ci.yml)
[![Release container images](https://github.com/TheNewThinkTank/container-factory/actions/workflows/release.yml/badge.svg)](https://github.com/TheNewThinkTank/container-factory/actions/workflows/release.yml)

# container-factory

A small, opinionated container-image factory for building, testing, scanning,
attesting, signing, and publishing multi-architecture container images.

## v2 supply-chain model

v2 makes the immutable image digest the identity of a release. The release
workflow:

1. validates image metadata;
2. builds and pushes `linux/amd64` and `linux/arm64` with Docker Buildx;
3. attaches an SBOM attestation;
4. attaches max-level BuildKit provenance;
5. records the resulting immutable digest;
6. scans the exact platform manifests behind that digest with Grype;
7. evaluates the factory security policy;
8. signs the exact multi-architecture digest with Sigstore/Cosign using GitHub
   Actions OIDC; and
9. verifies the signature before the job completes.

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
    └── release.yml
```

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
provenance: mode=max
sbom: true
```

BuildKit attaches these attestations to the pushed image rather than producing
only detached CI files.

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
export COSIGN_CERTIFICATE_IDENTITY='https://github.com/TheNewThinkTank/container-factory/.github/workflows/release.yml@refs/heads/main'
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
  exceptions: []
```

The release scan is performed against the exact child manifests for the
supported Linux architectures rather than against a separately rebuilt image.

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
export COSIGN_CERTIFICATE_IDENTITY='https://github.com/TheNewThinkTank/container-factory/.github/workflows/release.yml@refs/heads/main'
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

## v2 scope

v2 deliberately focuses on four supply-chain primitives:

- immutable OCI digests;
- SBOM attestations;
- SLSA/in-toto-style BuildKit provenance;
- keyless Sigstore/Cosign signatures and verification.

Admission control, policy engines, registry promotion, and consumer-side
verification beyond signature identity are intentionally left for later
versions.
