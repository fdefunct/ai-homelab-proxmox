from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build-ansible-known-hosts"


class BuildAnsibleKnownHostsTests(unittest.TestCase):
    def test_rebuilds_known_hosts_from_config_and_inventory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "scripts").mkdir()
            shutil.copy2(SCRIPT_PATH, repo_root / "scripts" / "build-ansible-known-hosts")

            (repo_root / "config").mkdir()
            (repo_root / "config" / "home.yaml").write_text(
                "terraform:\n"
                "  endpoint: https://pve-0.example.com:8006/api2/json\n"
            )

            inventory_path = repo_root / "ansible" / "inventories" / "home"
            inventory_path.mkdir(parents=True)
            (inventory_path / "generated.yml").write_text(
                "all:\n"
                "  children:\n"
                "    proxmox:\n"
                "      hosts:\n"
                "        pve-0:\n"
                "          ansible_host: 192.0.2.50\n"
                "    k3s:\n"
                "      hosts:\n"
                "        homelab-core-server-0:\n"
                "          ansible_host: 192.0.2.61\n"
                "        homelab-core-worker-0:\n"
                "          ansible_host: 192.0.2.61\n"
            )

            ssh_keyscan = repo_root / "ssh-keyscan"
            ssh_keyscan.write_text(
                "#!/bin/sh\n"
                "host=\"${3}\"\n"
                "printf '%s ssh-ed25519 %s\\n' \"$host\" \"$host-key\"\n"
            )
            ssh_keyscan.chmod(ssh_keyscan.stat().st_mode | stat.S_IXUSR)

            result = subprocess.run(
                [sys.executable, str(repo_root / "scripts" / "build-ansible-known-hosts"), "home"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                env={**os.environ, "SSH_KEYSCAN_BIN": str(ssh_keyscan)},
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            known_hosts_path = repo_root / ".ansible" / "known_hosts"
            self.assertTrue(known_hosts_path.exists())
            self.assertEqual(
                known_hosts_path.read_text().splitlines(),
                [
                    "pve-0.example.com ssh-ed25519 pve-0.example.com-key",
                    "192.0.2.50 ssh-ed25519 192.0.2.50-key",
                    "192.0.2.61 ssh-ed25519 192.0.2.61-key",
                ],
            )


if __name__ == "__main__":
    unittest.main()
