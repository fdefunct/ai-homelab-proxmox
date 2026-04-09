from __future__ import annotations

from pathlib import Path
import os
import stat
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run-ansible"


class RunAnsibleTests(unittest.TestCase):
    def test_fails_cleanly_when_known_hosts_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / ".venv" / "bin").mkdir(parents=True)
            (repo_root / "ansible" / "inventories" / "home").mkdir(parents=True)
            (repo_root / "ansible" / "playbooks").mkdir(parents=True)
            (repo_root / "Makefile").write_text("all:\n\t@true\n")
            (repo_root / "ansible" / "inventories" / "home" / "generated.yml").write_text("all: {}\n")
            (repo_root / "ansible" / "playbooks" / "site.yml").write_text("---\n")

            ansible_playbook = repo_root / ".venv" / "bin" / "ansible-playbook"
            ansible_playbook.write_text("#!/bin/sh\nexit 0\n")
            ansible_playbook.chmod(ansible_playbook.stat().st_mode | stat.S_IXUSR)

            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                env={**os.environ, "ENV_NAME": "home"},
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("make ENV=home ansible-known-hosts", result.stderr)


if __name__ == "__main__":
    unittest.main()
