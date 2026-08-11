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
scan:
  max_cvss: 7.0
```

The CI pipeline treats a successful security scan as a prerequisite for
publication.

## Why the image is built twice

v1 deliberately builds a local `linux/amd64` image first so vulnerability
analysis happens before publication. After that gate succeeds, Buildx performs
the actual multi-architecture build and pushes the result.

This is intentionally simple. v2 can move scanning into a more sophisticated
registry-independent promotion flow if required.
