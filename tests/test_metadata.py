import tempfile
import unittest
from pathlib import Path

import yaml

from container_factory.metadata import load_metadata


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


if __name__ == "__main__":
    unittest.main()
