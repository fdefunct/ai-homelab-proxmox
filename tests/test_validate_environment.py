from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

import yaml

from _helpers import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = load_script_module(REPO_ROOT / "scripts" / "validate-environment")
CONFIG = yaml.safe_load((REPO_ROOT / "config" / "home.yaml").read_text())


class ValidateEnvironmentTests(unittest.TestCase):
    def write_temp_config(self, config: dict) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        config_path = Path(temp_dir.name) / "home.yaml"
        config_path.write_text(yaml.safe_dump(config, sort_keys=False))
        return config_path

    def test_home_config_validates_cleanly(self):
        config_path = REPO_ROOT / "config" / "home.yaml"
        errors: list[str] = []

        MODULE.validate_json_schema(config_path, REPO_ROOT, errors)
        MODULE.validate_config("home", config_path, errors)

        self.assertEqual(errors, [])

    def test_rejects_unknown_ansible_key(self):
        config = copy.deepcopy(CONFIG)
        config["ansible"]["unexpected_key"] = True
        config_path = self.write_temp_config(config)
        errors: list[str] = []

        MODULE.validate_json_schema(config_path, REPO_ROOT, errors)

        self.assertEqual(len(errors), 1)
        self.assertIn("schema validation error", errors[0])
        self.assertIn("unexpected_key", errors[0])

    def test_rejects_removed_bootstrap_insecure_key(self):
        config = copy.deepcopy(CONFIG)
        config["terraform"]["bootstrap_insecure"] = True
        config_path = self.write_temp_config(config)
        errors: list[str] = []

        MODULE.validate_config("home", config_path, errors)

        self.assertIn(
            f"{config_path}: terraform.bootstrap_insecure has been removed; use BOOTSTRAP_PROXMOX_INSECURE=1 only as a temporary runtime override",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
