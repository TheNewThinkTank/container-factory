import re
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

    def test_syft_install_uses_sha_pinned_action(self):
        text = (ROOT / ".github/workflows/reusable-container.yml").read_text()
        self.assertIn('anchore/sbom-action/download-syft@3ad7283483fc7af8ff2b4ea19663c2d5ca935e26', text)
        self.assertIn('syft-version: "1.50.0"', text)
        self.assertNotIn('raw.githubusercontent.com/anchore/syft/main/install.sh', text)
        self.assertNotIn('| sh -s --', text)

    def test_actions_are_sha_pinned(self):
        reusable = (ROOT / ".github/workflows/reusable-container.yml").read_text()
        ci = (ROOT / ".github/workflows/ci.yml").read_text()

        expected_pins = [
            'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1',
            'docker/setup-buildx-action@37fe631027851001ddb9b187196cc803df7f5f0e',
            'docker/login-action@dbcb813823bdd20940b903addbd779551569679f',
            'docker/build-push-action@53b7df96c91f9c12dcc8a07bcb9ccacbed38856a',
            'sigstore/cosign-installer@6f9f17788090df1f26f669e9d70d6ae9567deba6',
            'anchore/scan-action/download-grype@e1165082ffb1fe366ebaf02d8526e7c4989ea9d2',
            'anchore/sbom-action/download-syft@3ad7283483fc7af8ff2b4ea19663c2d5ca935e26',
            'actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a',
            'actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830',
        ]
        for pin in expected_pins:
            self.assertIn(pin, reusable, f"missing SHA pin in reusable-container.yml: {pin}")

        # No mutable version tags on any `uses:` line in either workflow
        for wf_name, text in [("reusable-container.yml", reusable), ("ci.yml", ci)]:
            mutable = re.findall(r'uses:\s+\S+@v[\d.]+', text)
            self.assertFalse(mutable, f"{wf_name} has mutable action pins: {mutable}")

        # ci.yml checkout is also SHA-pinned
        self.assertIn('actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1', ci)
        self.assertIn('actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830', ci)

    def test_all_dockerfiles_run_as_non_root(self):
        for image in ("hello", "python", "node", "go", "nginx", "debian", "ubuntu"):
            text = (ROOT / "images" / image / "Dockerfile").read_text()
            self.assertIn("USER ", text, f"images/{image}/Dockerfile must set a non-root USER")

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
