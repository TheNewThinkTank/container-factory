import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

import yaml

from container_factory.metadata import load_metadata

ROOT = Path(__file__).resolve().parents[1]


def _load_validate_metadata_module():
    spec = importlib.util.spec_from_file_location(
        "validate_metadata",
        ROOT / "scripts" / "validate-metadata.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class MetadataTests(unittest.TestCase):
    def write_image(self, metadata: dict, dockerfile: str = "Dockerfile") -> Path:
        root = Path(tempfile.mkdtemp()) / "example"
        root.mkdir()
        (root / dockerfile).write_text("FROM scratch\n", encoding="utf-8")
        (root / "metadata.yaml").write_text(
            yaml.safe_dump(metadata), encoding="utf-8"
        )
        return root / "metadata.yaml"

    def valid_metadata(self) -> dict:
        return {
            "name": "example",
            "version": "1.2.3",
            "description": "Example image.",
            "dockerfile": "Dockerfile",
            "architectures": ["linux/amd64", "linux/arm64"],
            "registry": ["ghcr"],
        }

    def test_valid_metadata(self):
        path = self.write_image(self.valid_metadata())
        metadata = load_metadata(path)
        self.assertEqual(metadata["name"], "example")
        self.assertEqual(metadata["version"], "1.2.3")

    def test_missing_required_field(self):
        metadata = self.valid_metadata()
        del metadata["description"]
        path = self.write_image(metadata)
        with self.assertRaisesRegex(ValueError, "Missing required field"):
            load_metadata(path)

    def test_invalid_version(self):
        metadata = self.valid_metadata()
        metadata["version"] = "1.2"
        path = self.write_image(metadata)
        with self.assertRaisesRegex(ValueError, "valid SemVer"):
            load_metadata(path)

    def test_name_must_match_directory(self):
        metadata = self.valid_metadata()
        metadata["name"] = "different"
        path = self.write_image(metadata)
        with self.assertRaisesRegex(ValueError, "match the image directory"):
            load_metadata(path)

    def test_dockerfile_must_exist(self):
        metadata = self.valid_metadata()
        metadata["dockerfile"] = "Containerfile"
        path = self.write_image(metadata)
        with self.assertRaisesRegex(ValueError, "Dockerfile referenced"):
            load_metadata(path)

    def test_parent_traversal_is_rejected(self):
        metadata = self.valid_metadata()
        metadata["dockerfile"] = "../Dockerfile"
        path = self.write_image(metadata)
        with self.assertRaisesRegex(ValueError, "relative path"):
            load_metadata(path)

    def test_duplicate_architecture_is_rejected(self):
        metadata = self.valid_metadata()
        metadata["architectures"] = ["linux/amd64", "linux/amd64"]
        path = self.write_image(metadata)
        with self.assertRaisesRegex(ValueError, "must not contain duplicates"):
            load_metadata(path)

    def test_unsupported_architecture_is_rejected(self):
        metadata = self.valid_metadata()
        metadata["architectures"] = ["linux/s390x"]
        path = self.write_image(metadata)
        with self.assertRaisesRegex(ValueError, "Unsupported architecture"):
            load_metadata(path)

    def test_unsupported_registry_is_rejected(self):
        metadata = self.valid_metadata()
        metadata["registry"] = ["dockerhub"]
        path = self.write_image(metadata)
        with self.assertRaisesRegex(ValueError, "Unsupported registry"):
            load_metadata(path)

    def test_unknown_field_is_rejected(self):
        metadata = self.valid_metadata()
        metadata["architektures"] = ["linux/amd64"]  # typo alongside valid field
        path = self.write_image(metadata)
        with self.assertRaisesRegex(ValueError, "Unknown field"):
            load_metadata(path)


class WriteGithubOutputsTests(unittest.TestCase):
    def test_writes_name_and_version_to_github_output(self):
        mod = _load_validate_metadata_module()
        metadata = {"name": "myimage", "version": "1.2.3"}
        with tempfile.NamedTemporaryFile(mode="r", suffix=".env", delete=False) as f:
            output_path = f.name
        try:
            os.environ["GITHUB_OUTPUT"] = output_path
            mod.write_github_outputs(metadata)
            content = Path(output_path).read_text(encoding="utf-8")
            self.assertIn("name=myimage\n", content)
            self.assertIn("version=1.2.3\n", content)
        finally:
            del os.environ["GITHUB_OUTPUT"]
            Path(output_path).unlink(missing_ok=True)

    def test_skips_write_when_github_output_unset(self):
        mod = _load_validate_metadata_module()
        os.environ.pop("GITHUB_OUTPUT", None)
        mod.write_github_outputs({"name": "x", "version": "0.0.1"})


if __name__ == "__main__":
    unittest.main()
