#!/usr/bin/env python3
"""Validate the deliberately small YAML metadata format used by container-factory."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_ROOT = ROOT / "images"

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")

# Sections that should be lists
LIST_SECTIONS = {"architectures", "registry"}


def parse_metadata(path: Path) -> dict:
    data: dict = {}
    section = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if line.startswith("- "):
            if section is None or not isinstance(data.get(section), list):
                raise ValueError(f"{path}: list item without list key")
            data[section].append(line[2:].strip().strip('"').strip("'"))
            continue

        if ":" not in line:
            raise ValueError(f"{path}: unsupported YAML line: {raw!r}")

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if indent and section:
            if not isinstance(data[section], dict):
                raise ValueError(f"{path}: unexpected nested value")
            data[section][key] = value.strip('"').strip("'")
        elif not value:
            # An empty top-level value starts either a list or a mapping.
            section = key
            # Initialize as list if this is a known list section, otherwise as dict
            data[key] = [] if key in LIST_SECTIONS else {}
        else:
            section = None
            data[key] = value.strip('"').strip("'")

    return data


def main() -> int:
    errors = []

    for metadata in sorted(IMAGE_ROOT.glob("*/metadata.yaml")):
        image_dir = metadata.parent

        try:
            data = parse_metadata(metadata)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        required = {"name", "version", "description", "dockerfile", "architectures", "registry"}
        missing = required - data.keys()
        if missing:
            errors.append(f"{metadata}: missing keys: {', '.join(sorted(missing))}")
            continue

        if not NAME_RE.fullmatch(str(data["name"])):
            errors.append(f"{metadata}: invalid image name: {data['name']!r}")

        if not VERSION_RE.fullmatch(str(data["version"])):
            errors.append(f"{metadata}: version must be semantic X.Y.Z: {data['version']!r}")

        dockerfile = image_dir / str(data["dockerfile"])
        if not dockerfile.is_file():
            errors.append(f"{metadata}: Dockerfile not found: {dockerfile}")

        architectures = data["architectures"]
        if not isinstance(architectures, list) or not architectures:
            errors.append(f"{metadata}: architectures must be a non-empty list")
        elif any(a not in {"linux/amd64", "linux/arm64"} for a in architectures):
            errors.append(f"{metadata}: unsupported architecture: {architectures}")

        registries = data["registry"]
        if not isinstance(registries, list) or not registries:
            errors.append(f"{metadata}: registry must be a non-empty list")
        elif any(r not in {"ghcr", "dockerhub"} for r in registries):
            errors.append(f"{metadata}: unsupported registry: {registries}")


    if errors:
        print("Metadata validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Metadata validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
