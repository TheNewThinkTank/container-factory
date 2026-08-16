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

    def test_node_runtime_omits_npm_toolchain(self):
        text = (ROOT / "images/node/Dockerfile").read_text()
        self.assertIn("rm -rf /usr/local/lib/node_modules/npm", text)
        self.assertIn("rm -f /usr/local/bin/npm /usr/local/bin/npx", text)
        self.assertNotIn("npm install --global", text)

    def test_syft_install_uses_official_pinned_installer(self):
        text = (ROOT / ".github/workflows/reusable-container.yml").read_text()
        self.assertIn('SYFT_VERSION: "1.50.0"', text)
        self.assertIn('https://raw.githubusercontent.com/anchore/syft/main/install.sh', text)
        self.assertIn('sh -s -- -b "$install_dir" -v "v${SYFT_VERSION}"', text)
        self.assertIn("--retry 5", text)
        self.assertIn('sigstore/cosign-installer@v4.1.2', text)
        self.assertIn('test -x "$install_dir/syft"', text)
        self.assertIn('echo "$install_dir" >> "$GITHUB_PATH"', text)
        self.assertNotIn("anchore/sbom-action/download-syft@v0", text)
        self.assertNotIn('syft/releases/download', text)
        self.assertNotIn('syft-download', text)

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
