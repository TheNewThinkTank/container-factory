#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

import yaml


REQUIRED_FIELDS = {
    "name",
    "version",
}


def load_metadata(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Metadata file does not exist: {path}")

    try:
        with path.open(encoding="utf-8") as f:
            metadata = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise SystemExit(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(metadata, dict):
        raise SystemExit(f"Metadata must be a YAML mapping: {path}")

    return metadata


def get_required(metadata: dict, key: str, path: Path) -> str:
    if key not in metadata:
        raise SystemExit(f"Missing '{key}' in {path}")

    value = metadata[key]

    if value is None or str(value).strip() == "":
        raise SystemExit(f"'{key}' cannot be empty in {path}")

    return str(value).strip()


def validate(path: Path) -> dict:
    metadata = load_metadata(path)

    for key in REQUIRED_FIELDS:
        get_required(metadata, key, path)

    return metadata


def write_github_outputs(metadata: dict) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")

    if not github_output:
        return

    with open(github_output, "a", encoding="utf-8") as f:
        f.write(f"name={metadata['name']}\n")
        f.write(f"version={metadata['version']}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate container image metadata."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to metadata.yaml",
    )

    args = parser.parse_args()

    metadata = validate(args.path)

    print(f"Metadata validated: {args.path}")
    print(f"  name: {metadata['name']}")
    print(f"  version: {metadata['version']}")

    write_github_outputs(metadata)

    return 0


if __name__ == "__main__":
    sys.exit(main())
