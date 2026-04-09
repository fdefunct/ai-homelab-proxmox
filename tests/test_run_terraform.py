from __future__ import annotations

from pathlib import Path
import os
import stat
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run-terraform"


class RunTerraformTests(unittest.TestCase):
    def test_bootstrap_override_is_runtime_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "scripts").mkdir()
            (repo_root / "terraform" / "envs" / "home").mkdir(parents=True)
            (repo_root / "bin").mkdir()
            (repo_root / "Makefile").write_text("all:\n\t@true\n")
            (repo_root / "terraform" / "envs" / "home" / "generated.auto.tfvars.json").write_text("{}\n")

            render_script = repo_root / "scripts" / "render-terraform-secrets"
            render_script.write_text("#!/bin/sh\nprintf 'proxmox_api_token = \"token\"\\n'\n")
            render_script.chmod(render_script.stat().st_mode | stat.S_IXUSR)

            assert_script = repo_root / "scripts" / "assert-rendered-secrets"
            assert_script.write_text("#!/bin/sh\nexit 0\n")
            assert_script.chmod(assert_script.stat().st_mode | stat.S_IXUSR)

            terraform_bin = repo_root / "bin" / "terraform"
            terraform_bin.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$*\" > \"$ARG_LOG\"\n"
            )
            terraform_bin.chmod(terraform_bin.stat().st_mode | stat.S_IXUSR)

            arg_log = repo_root / "terraform-args.txt"
            result = subprocess.run(
                ["/bin/bash", str(SCRIPT_PATH), "plan"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "ENV_NAME": "home",
                    "BOOTSTRAP_PROXMOX_INSECURE": "1",
                    "PATH": f"{repo_root / 'bin'}:{os.environ['PATH']}",
                    "ARG_LOG": str(arg_log),
                },
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Day 0-only insecure TLS override", result.stderr)
            self.assertIn("-var=proxmox_insecure=true", arg_log.read_text())


if __name__ == "__main__":
    unittest.main()
