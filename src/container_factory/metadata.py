"""Validation and loading of container-factory image metadata."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

REQUIRED_FIELDS = frozenset(
    {
        "name",
        "version",
        "description",
        "dockerfile",
        "architectures",
        "registry",
    }
)

SUPPORTED_ARCHITECTURES = frozenset({"linux/amd64", "linux/arm64"})
SUPPORTED_REGISTRIES = frozenset({"ghcr"})
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def _require_non_empty_string(metadata: dict[str, Any], key: str, path: Path) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{key}' must be a non-empty string in {path}")
    return value.strip()


def _require_unique_list(
    metadata: dict[str, Any], key: str, path: Path
) -> list[str]:
    value = metadata.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"'{key}' must be a non-empty list in {path}")

    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"'{key}' must contain non-empty strings in {path}")

    values = [item.strip() for item in value]
    if len(values) != len(set(values)):
        raise ValueError(f"'{key}' must not contain duplicates in {path}")
    return values


def load_metadata(path: Path) -> dict[str, Any]:
    """Load and validate one image's metadata.yaml file."""
    path = path.resolve()

    if not path.is_file():
        raise ValueError(f"Metadata file does not exist: {path}")

    try:
        metadata = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(metadata, dict):
        raise ValueError(f"Metadata must be a YAML mapping: {path}")

    missing = REQUIRED_FIELDS - metadata.keys()
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing required field(s) in {path}: {missing_text}")

    name = _require_non_empty_string(metadata, "name", path)
    version = _require_non_empty_string(metadata, "version", path)
    description = _require_non_empty_string(metadata, "description", path)
    dockerfile = _require_non_empty_string(metadata, "dockerfile", path)
    architectures = _require_unique_list(metadata, "architectures", path)
    registries = _require_unique_list(metadata, "registry", path)

    if not NAME_RE.fullmatch(name):
        raise ValueError(
            f"'name' must contain only lowercase letters, digits, '.', '_' or '-': {name}"
        )

    if name != path.parent.name:
        raise ValueError(
            f"'name' must match the image directory name ({path.parent.name!r}): {name!r}"
        )

    if not SEMVER_RE.fullmatch(version):
        raise ValueError(f"'version' must be valid SemVer: {version!r}")

    dockerfile_path = path.parent / dockerfile
    if Path(dockerfile).is_absolute() or ".." in Path(dockerfile).parts:
        raise ValueError(f"'dockerfile' must be a relative path inside the image directory: {dockerfile!r}")
    if not dockerfile_path.is_file():
        raise ValueError(f"Dockerfile referenced by metadata does not exist: {dockerfile_path}")

    unsupported_architectures = set(architectures) - SUPPORTED_ARCHITECTURES
    if unsupported_architectures:
        values = ", ".join(sorted(unsupported_architectures))
        raise ValueError(f"Unsupported architecture(s) in {path}: {values}")

    unsupported_registries = set(registries) - SUPPORTED_REGISTRIES
    if unsupported_registries:
        values = ", ".join(sorted(unsupported_registries))
        raise ValueError(f"Unsupported registry/registries in {path}: {values}")

    return {
        **metadata,
        "name": name,
        "version": version,
        "description": description,
        "dockerfile": dockerfile,
        "architectures": architectures,
        "registry": registries,
    }
