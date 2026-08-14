#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from container_factory.metadata import load_metadata  # noqa: E402


def write_github_outputs(metadata: dict[str, object]) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        return

    with open(github_output, "a", encoding="utf-8") as f:
        f.write(f"name={metadata['name']}\n")
        f.write(f"version={metadata['version']}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate container image metadata.")
    parser.add_argument("path", type=Path, help="Path to metadata.yaml")
    args = parser.parse_args()

    try:
        metadata = load_metadata(args.path)
    except ValueError as exc:
        print(f"Metadata validation FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Metadata validated: {args.path}")
    print(f"  name:          {metadata['name']}")
    print(f"  version:       {metadata['version']}")
    print(f"  dockerfile:    {metadata['dockerfile']}")
    print(f"  architectures: {', '.join(metadata['architectures'])}")
    print(f"  registry:      {', '.join(metadata['registry'])}")

    write_github_outputs(metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
