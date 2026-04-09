from __future__ import annotations

from pathlib import Path
import unittest

import yaml

from _helpers import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = load_script_module(REPO_ROOT / "scripts" / "generate-config")
CONFIG = yaml.safe_load((REPO_ROOT / "config" / "home.yaml").read_text())


class GenerateConfigTests(unittest.TestCase):
    def test_build_gateways_inherits_defaults(self):
        gateways = MODULE.build_gateways(CONFIG)
        alpha_gateway = gateways["vm-alpha-gw"]

        self.assertEqual(alpha_gateway["cpu_cores"], CONFIG["gateways"]["defaults"]["cpu_cores"])
        self.assertEqual(alpha_gateway["memory_mb"], CONFIG["gateways"]["defaults"]["memory_mb"])
        self.assertEqual(alpha_gateway["start_on_boot"], CONFIG["gateways"]["defaults"]["start_on_boot"])
        self.assertEqual(alpha_gateway["install_tailscale"], CONFIG["gateways"]["defaults"]["install_tailscale"])
        self.assertEqual(alpha_gateway["inventory_groups"], CONFIG["gateways"]["defaults"]["inventory_groups"])
        self.assertTrue(alpha_gateway["caddy"]["enabled"])

    def test_build_terraform_vars_contains_expected_keys(self):
        terraform_vars = MODULE.build_terraform_vars(CONFIG)

        self.assertEqual(terraform_vars["cluster_operator_user"], CONFIG["ansible"]["operator_user"])
        self.assertEqual(terraform_vars["proxmox_endpoint"], CONFIG["terraform"]["endpoint"])
        self.assertEqual(terraform_vars["proxmox_management_dns_servers"], CONFIG["network"]["management_dns_servers"])
        self.assertNotIn("proxmox_bootstrap_insecure_allowed", terraform_vars)
        self.assertIn("homelab-core-server-0", terraform_vars["cluster_nodes"])
        self.assertIn("vm-alpha-gw", terraform_vars["openclaw_gateways"])

    def test_build_inventory_contains_expected_groups_and_hosts(self):
        inventory = MODULE.build_inventory(CONFIG)
        children = inventory["all"]["children"]

        self.assertIn("k3s_server", children)
        self.assertIn("k3s_agents", children)
        self.assertIn("openclaw_gateways", children)
        self.assertIn("homelab-core-server-0", children["k3s_server"]["hosts"])
        self.assertIn("vm-alpha-gw", children["openclaw_gateways"]["hosts"])
        self.assertEqual(inventory["all"]["vars"]["platform_cluster_name"], CONFIG["platform"]["cluster_name"])
        self.assertEqual(inventory["all"]["vars"]["k3s_server_name"], "homelab-core-server-0")


if __name__ == "__main__":
    unittest.main()
