from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate-secret-catalog"


class ValidateSecretCatalogTests(unittest.TestCase):
    def test_rejects_unexpected_op_reference_outside_allowed_files(self):
        op_prefix = "op" + "://"

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "scripts").mkdir()
            shutil.copy2(SCRIPT_PATH, repo_root / "scripts" / "validate-secret-catalog")

            (repo_root / "docs").mkdir()
            (repo_root / "docs" / "secret-catalog.yaml").write_text(
                "references:\n"
                f"  - ref: {op_prefix}Homelab/pve-0-bootstrap/username\n"
                "    owner: bootstrap\n"
                "    purpose: Test bootstrap username.\n"
                "    consumers:\n"
                "      - ansible/bootstrap-ssh-user\n"
            )

            (repo_root / "config").mkdir()
            (repo_root / "config" / "home.yaml").write_text(
                "platform:\n"
                "  onepassword_vault: Homelab\n"
            )

            for relative_path in (
                "ansible/secrets.yml",
                "ansible/bootstrap-ssh-private-key",
                "ansible/bootstrap-ssh-user",
                "ansible/operator-ssh-private-key",
                "ansible/argocd-repo-private-key",
                "terraform/envs/home/secrets.tfvars.template",
            ):
                path = repo_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("")

            (repo_root / "ansible" / "bootstrap-ssh-user").write_text(f"{op_prefix}Homelab/pve-0-bootstrap/username\n")

            unexpected_path = repo_root / "kubernetes" / "manifests" / "platform" / "bad.yaml"
            unexpected_path.parent.mkdir(parents=True, exist_ok=True)
            unexpected_path.write_text(f'token: "{op_prefix}Homelab/unexpected/credential"\n')

            result = subprocess.run(
                [sys.executable, str(repo_root / "scripts" / "validate-secret-catalog"), "home"],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected 1Password reference(s)", result.stderr)
            self.assertIn("kubernetes/manifests/platform/bad.yaml", result.stderr)


if __name__ == "__main__":
    unittest.main()
