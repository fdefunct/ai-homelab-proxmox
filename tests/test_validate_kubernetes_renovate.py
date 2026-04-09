from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

import yaml

from _helpers import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = load_script_module(REPO_ROOT / "scripts" / "validate_kubernetes_renovate.py")
CONFIG = yaml.safe_load((REPO_ROOT / "config" / "home.yaml").read_text())


class ValidateKubernetesRenovateTests(unittest.TestCase):
    def test_rejects_missing_digest_pinning_helper(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            shutil.copytree(REPO_ROOT / ".renovate", repo_root / ".renovate")
            shutil.copytree(REPO_ROOT / "config", repo_root / "config")
            shutil.copytree(REPO_ROOT / "kubernetes", repo_root / "kubernetes")
            shutil.copytree(REPO_ROOT / "kubernetes" / "apps", repo_root / "kubernetes" / "apps", dirs_exist_ok=True)
            shutil.copy2(REPO_ROOT / ".renovaterc.json5", repo_root / ".renovaterc.json5")

            renovate_config_path = repo_root / ".renovaterc.json5"
            renovate_config_path.write_text(renovate_config_path.read_text().replace('"helpers:pinGitHubActionDigests",\n', ""))

            errors: list[str] = []
            MODULE.validate(repo_root, CONFIG, errors)

            self.assertIn(
                ".renovaterc.json5: extends must pin GitHub Action digests",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
