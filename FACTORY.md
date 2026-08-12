# Factory contract

An image definition is a directory under `images/` containing:

- `Dockerfile`
- `metadata.yaml`

The metadata contract is:

```yaml
name: <lowercase image name>
version: <semver>
description: <human-readable description>
dockerfile: Dockerfile
architectures:
  - linux/amd64
  - linux/arm64
registry:
  - ghcr
```

Security policy is global and lives in `.config/security-policy.yaml`.

## Security gate

The factory uses Syft to generate an SBOM and Grype to produce a JSON
vulnerability report. `src/container_factory/security/policy.py` evaluates
that report.

The default policy:

- fails on Critical findings when a fix is available;
- fails on High findings with CVSS >= 7.0 when a fix is available;
- reports Critical/High findings with no known fix for review;
- ignores Medium, Low, Negligible and Unknown findings;
- supports explicit, time-limited exceptions;
- fails when an exception has expired.

A finding with no available fix is therefore visible in CI rather than being
silently ignored. `no_fix_action` can be changed from `review` to `fail` when
a stricter fail-closed policy is desired.

Exceptions require:

```yaml
exceptions:
  - id: CVE-XXXX-YYYY
    reason: "Document why accepting the risk is justified."
    expires: 2026-09-30
```

Exceptions must expire. This prevents temporary risk acceptance from becoming
permanent.

## Why the image is built twice

v1 builds a local `linux/amd64` image first so vulnerability analysis happens
before publication. After that gate succeeds, Buildx performs the actual
multi-architecture build and pushes the result.

## Local usage

Requirements:

- Docker
- Docker Buildx
- Bash
- Python 3.11+
- `syft`
- `grype`

Set up the policy environment once:

```bash
make setup
```

Validate the repository:

```bash
make validate
```

Run security-policy tests:

```bash
make test
```

Build an image:

```bash
make build IMAGE=python
```

Generate an SBOM:

```bash
make sbom IMAGE=python
```

Scan an image:

```bash
make scan IMAGE=python
```

Run the complete local pipeline:

```bash
make security IMAGE=python
```

Security reports are written to `reports/` and SBOMs to `sbom/`.

## CI behaviour

Pull requests and pushes run:

- metadata validation
- security-policy validation and unit tests
- local image build
- SBOM generation
- Grype vulnerability scanning
- the global security policy

Release publication happens only after the security gate succeeds.

## Design principles

### Security policy is separate from scanning

Grype reports facts. The factory's policy decides what those facts mean for
publication. This avoids encoding project policy in a scanner command-line
flag.

### No-fix findings remain visible

A Critical or High vulnerability marked as `won't fix` does not disappear.
It is reported as a review finding. An explicit exception can document an
accepted risk.

### Fail closed for expired exceptions

An expired exception is a policy failure.

### Keep the factory boring

The repository uses GitHub Actions, Docker Buildx, Syft, Grype and a small
Python policy module rather than a large custom framework.

## Roadmap

Potential future additions:

- Cosign image signing
- SLSA provenance
- registry promotion
- Docker Hub publishing
- digest pinning
- automated base-image rebuilds
- SARIF results in GitHub Security
- reusable workflows
- image catalogue generation
