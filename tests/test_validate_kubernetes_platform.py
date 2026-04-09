from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

import yaml

from _helpers import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = load_script_module(REPO_ROOT / "scripts" / "validate_kubernetes_platform.py")
CONFIG = yaml.safe_load((REPO_ROOT / "config" / "home.yaml").read_text())


class ValidateKubernetesPlatformTests(unittest.TestCase):
    def test_rejects_gatus_endpoint_drift(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            shutil.copytree(REPO_ROOT / "config", repo_root / "config")
            shutil.copytree(REPO_ROOT / "kubernetes", repo_root / "kubernetes")

            gatus_values_path = repo_root / "kubernetes" / "charts" / "gatus" / "values.yaml"
            gatus_values = yaml.safe_load(gatus_values_path.read_text())
            gatus_values["config"]["endpoints"] = []
            gatus_values_path.write_text(yaml.safe_dump(gatus_values, sort_keys=False))

            errors: list[str] = []
            MODULE.validate(repo_root, CONFIG, errors)

            self.assertIn(
                "kubernetes/charts/gatus/values.yaml: config.endpoints must match scripts/render-gatus-config output",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
