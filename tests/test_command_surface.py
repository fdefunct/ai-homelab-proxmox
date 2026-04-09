from __future__ import annotations

from pathlib import Path
import json
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class CommandSurfaceTests(unittest.TestCase):
    def test_package_scripts_delegate_to_make(self):
        package = json.loads((REPO_ROOT / "package.json").read_text())

        self.assertEqual(package["scripts"]["format"], "make format")
        self.assertEqual(package["scripts"]["format:check"], "make format-check")

    def test_ci_workflows_use_make_for_repo_validators(self):
        ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
        kubernetes_pr_workflow = (REPO_ROOT / ".github" / "workflows" / "kubernetes-pr.yml").read_text()

        for expected in (
            "make ENV=${{ env.ENV }} generate-config",
            "make ENV=${{ env.ENV }} env-validate",
            "make ENV=${{ env.ENV }} tf-validate",
            "make ENV=${{ env.ENV }} tf-lint",
            "make ENV=${{ env.ENV }} ansible-syntax",
            "make format-check",
            "make yaml-lint",
            "make shell-lint",
            "make ENV=${{ env.ENV }} checkov-validate",
            "make ENV=${{ env.ENV }} kubernetes-validate",
            "make ENV=${{ env.ENV }} secret-catalog-validate",
        ):
            self.assertIn(expected, ci_workflow)

        self.assertIn("make ENV=${{ env.ENV }} generate-config", kubernetes_pr_workflow)


if __name__ == "__main__":
    unittest.main()
