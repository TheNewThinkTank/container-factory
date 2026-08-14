
[![CI](https://github.com/TheNewThinkTank/container-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/TheNewThinkTank/container-factory/actions/workflows/ci.yml)

[![Release container images](https://github.com/TheNewThinkTank/container-factory/actions/workflows/release.yml/badge.svg)](https://github.com/TheNewThinkTank/container-factory/actions/workflows/release.yml)

# container-factory

A small, opinionated container-image factory for building, testing, scanning, generating SBOMs, and publishing multi-architecture container images.

The v1 implementation is designed around:

- GitHub Actions
- Docker Buildx / BuildKit
- `linux/amd64` and `linux/arm64`
- Grype vulnerability scanning
- SBOM generation with Syft
- a configurable CVSS security gate
- GitHub Container Registry (GHCR)
- immutable versioned image tags
- Dependabot for dependency/base-image maintenance
- local development through a Makefile

## Repository layout

```text
container-factory/
├── images/
│   ├── hello/
│   │   ├── Dockerfile
│   │   └── metadata.yaml
│   └── python/
│       ├── Dockerfile
│       └── metadata.yaml
├── scripts/
│   ├── build-image.sh
│   ├── scan-image.sh
│   ├── security-policy.sh
│   ├── setup-security-tools.sh
│   ├── generate-sbom.sh
│   └── validate-metadata.py
├── src/
│   └── container_factory/
│       └── security/
│           └── policy.py
├── tests/
│   └── test_security_policy.py
├── requirements-dev.txt
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── release.yml
│   └── dependabot.yml
├── .config/
│   └── security-policy.yaml
├── Makefile
├── compose.yaml
├── .dockerignore
└── .gitignore
```

`hello` is intentionally tiny and acts as an end-to-end smoke-test image. `python` demonstrates a useful real image definition.

## Image metadata

Each image has a `metadata.yaml`:

```yaml
name: python
version: "3.14"
description: Python runtime based on Debian Trixie slim.
dockerfile: Dockerfile
architectures:
  - linux/amd64
  - linux/arm64
registry:
  - ghcr
scan:
  max_cvss: 7.0
```

The metadata is deliberately simple in v1. The CI workflow discovers changed image directories and uses the metadata to determine how an image should be built and published.

## Security policy

The security policy is global and lives in `.config/security-policy.yaml`.

Grype is used to discover vulnerabilities; the factory's Python policy engine
decides whether they block publication.

The default policy is:

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

This means:

| Finding | Result |
|---|---|
| Critical + fix available | **Fail** |
| High + CVSS >= 7 + fix available | **Fail** |
| Critical/High + no known fix | **Review** |
| Medium/Low/Negligible/Unknown | **Ignore** |
| Active documented exception | **Allow** |
| Expired exception | **Fail** |

A `won't fix` finding is therefore not silently ignored. It remains visible in
the CI output and can be accepted only with a documented, time-limited
exception when appropriate:

```yaml
exceptions:
  - id: CVE-XXXX-YYYY
    reason: "Document why accepting the risk is justified."
    expires: 2026-09-30
```

Exceptions are deliberately required to expire.

The policy is separate from Grype's `--fail-on` option so that scanner output
and publication policy remain independent.

## Local usage

Requirements:

- Docker
- Docker Buildx
- Bash
- Python 3.11+
- `syft`
- `grype`
- Python 3.11+
- PyYAML (installed by `make setup`)

Validate the repository:

```bash
make setup
make validate
make test
```

Build an image:

```bash
make build IMAGE=hello
```

Generate an SBOM:

```bash
make sbom IMAGE=hello
```

Scan an image:

```bash
make scan IMAGE=hello
```

Run the full local security pipeline:

```bash
make security IMAGE=hello
```

The local scripts use the same policy file as CI.

## GitHub setup

Create a GitHub repository and push this directory.

The release workflow uses GitHub's built-in `GITHUB_TOKEN` to publish to GHCR. In the repository settings, ensure Actions have permission to write packages:

**Settings → Actions → General → Workflow permissions → Read and write permissions**

The workflow also explicitly requests:

```yaml
permissions:
  contents: read
  packages: write
```

No registry password is required for GHCR.

## Image names and tags

Published images use:

```text
ghcr.io/<github-owner>/<image-name>:<version>
ghcr.io/<github-owner>/<image-name>:<major>
ghcr.io/<github-owner>/<image-name>:<major>.<minor>
ghcr.io/<github-owner>/<image-name>:latest
```

`latest` is only updated for a release on the default branch.

The version is currently taken from `metadata.yaml`. In a future version, this can be replaced by Git tags or a release manifest.

## CI behaviour

Pull requests run:

- metadata validation
- Dockerfile syntax/build checks
- local image build
- SBOM generation
- vulnerability scanning

Pushes to the default branch run the same checks.

A release is published when an image's `metadata.yaml` changes its version, or when the workflow is manually dispatched.

## Design principles

### Fail closed

A security failure prevents publication.

### Reproducible enough

Images pin major/minor runtime versions in metadata and use explicit Dockerfiles. Digest pinning can be added in v2.

### Multi-architecture by default

Images are built for:

```text
linux/amd64
linux/arm64
```

This is useful for x86 servers, Apple Silicon development machines, and ARM homelab nodes.

### Keep the factory boring

The repository intentionally avoids a custom build framework in v1. GitHub Actions, Docker Buildx, Syft, and Grype are mature tools and are easier to understand and maintain than a bespoke abstraction.

## Roadmap

Potential v2 additions:

- Cosign image signing
- SLSA provenance
- registry promotion
- Docker Hub publishing
- digest pinning
- automated base-image rebuilds
- policy exceptions with expiry dates
- SARIF results in GitHub Security
- reusable workflows for other repositories
- image catalogue generation
