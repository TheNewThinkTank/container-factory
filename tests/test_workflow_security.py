import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WorkflowSecurityTests(unittest.TestCase):
    def test_release_does_not_reference_matrix_in_job_if(self):
        text = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertNotIn("if: github.ref == 'refs/heads/main'", text)
        self.assertNotIn("matrix.image)", text)

    def test_release_matrix_contains_all_images(self):
        text = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertIn("image:\n          - hello\n          - python", text)

    def test_signing_identity_is_reusable_workflow(self):
        text = (ROOT / ".github/workflows/reusable-container.yml").read_text()
        expected = "https://github.com/${{ github.repository }}/.github/workflows/reusable-container.yml@refs/heads/main"
        self.assertIn(expected, text)
        self.assertNotIn(".github/workflows/release.yml@refs/heads/main", text)

    def test_release_matrix_contains_all_factory_images(self):
        text = (ROOT / ".github/workflows/release.yml").read_text()
        for image in ("hello", "python", "node", "go", "nginx", "debian", "ubuntu"):
            self.assertIn(f"          - {image}", text)

    def test_node_uses_requested_trixie_image(self):
        text = (ROOT / "images/node/Dockerfile").read_text()
        self.assertIn("FROM node:26.7-trixie-slim", text)
        self.assertNotIn("bookworm", text.lower())

    def test_node_pins_patched_npm_release(self):
        text = (ROOT / "images/node/Dockerfile").read_text()
        self.assertIn("npm install --global npm@12.0.1", text)
        self.assertNotIn("npm install --global npm@latest", text)

    def test_go_uses_requested_trixie_image(self):
        text = (ROOT / "images/go/Dockerfile").read_text()
        self.assertIn("FROM golang:1.26.6-trixie", text)
        self.assertNotIn("bookworm", text.lower())

    def test_reusable_workflow_has_no_elevated_permissions(self):
        text = (ROOT / ".github/workflows/reusable-container.yml").read_text()
        self.assertNotIn("packages: write", text)
        self.assertNotIn("id-token: write", text)


if __name__ == "__main__":
    unittest.main()
