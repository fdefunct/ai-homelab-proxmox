from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

from _helpers import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = load_script_module(REPO_ROOT / "scripts" / "validate_kubernetes_apps.py")


class ValidateKubernetesAppsTests(unittest.TestCase):
    def test_rejects_multi_source_app_without_repo_values_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "config").mkdir()
            (repo_root / "config" / "home.yaml").write_text(
                "ansible:\n"
                "  argocd_repo_url: git@github.com:your-github-user/ai-homelab-proxmox.git\n"
            )

            apps_dir = repo_root / "kubernetes" / "apps"
            (apps_dir / "platform" / "demo").mkdir(parents=True)
            (apps_dir / "root-app.yaml").write_text(
                yaml.safe_dump(
                    {
                        "apiVersion": "argoproj.io/v1alpha1",
                        "kind": "Application",
                        "metadata": {"name": "root-app", "namespace": "argocd"},
                        "spec": {
                            "source": {
                                "repoURL": "git@github.com:your-github-user/ai-homelab-proxmox.git",
                                "path": "kubernetes/apps",
                            }
                        },
                    },
                    sort_keys=False,
                )
            )
            (apps_dir / "platform" / "demo" / "application.yaml").write_text(
                yaml.safe_dump(
                    {
                        "apiVersion": "argoproj.io/v1alpha1",
                        "kind": "Application",
                        "metadata": {"name": "demo", "namespace": "argocd"},
                        "spec": {
                            "sources": [
                                {
                                    "repoURL": "https://charts.example.com",
                                    "chart": "demo",
                                    "targetRevision": "1.2.3",
                                }
                            ]
                        },
                    },
                    sort_keys=False,
                )
            )

            config = yaml.safe_load((repo_root / "config" / "home.yaml").read_text())
            errors: list[str] = []

            MODULE.validate(repo_root, config, errors)

            self.assertIn(
                f"{apps_dir / 'platform' / 'demo' / 'application.yaml'}: multi-source app must include repo values source for this repo",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
