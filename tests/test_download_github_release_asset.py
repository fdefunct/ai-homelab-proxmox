from __future__ import annotations

from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import subprocess
import tempfile
from threading import Thread
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "download-github-release-asset"


class DownloadGithubReleaseAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.version = "1.2.3"
        self.repo_name = "example/tools"
        self.asset_name = "tool-linux-amd64.tar.gz"
        self.checksum_asset_name = "CHECKSUMS"
        self.asset_content = b"release asset contents\n"
        self.asset_sha = hashlib.sha256(self.asset_content).hexdigest()

        self.release_dir = self.repo_root / "example" / "tools" / "releases" / "download" / f"v{self.version}"
        self.release_dir.mkdir(parents=True)
        (self.release_dir / self.asset_name).write_bytes(self.asset_content)
        self.destination = self.repo_root / "downloads" / self.asset_name

        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                return

        handler = partial(QuietHandler, directory=str(self.repo_root))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=5)
        self.temp_dir.cleanup()

    def run_helper(self):
        return subprocess.run(
            [
                "/bin/bash",
                str(SCRIPT_PATH),
                self.repo_name,
                self.version,
                self.asset_name,
                self.checksum_asset_name,
                str(self.destination),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "GITHUB_RELEASE_BASE_URL": self.base_url},
        )

    def test_download_succeeds_when_checksum_matches(self):
        (self.release_dir / self.checksum_asset_name).write_text(f"{self.asset_sha}  {self.asset_name}\n")

        result = self.run_helper()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(self.destination.read_bytes(), self.asset_content)

    def test_download_fails_when_checksum_mismatches(self):
        (self.release_dir / self.checksum_asset_name).write_text(f"{'0' * 64}  {self.asset_name}\n")

        result = self.run_helper()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Checksum mismatch", result.stderr)

    def test_download_fails_when_checksum_entry_missing(self):
        (self.release_dir / self.checksum_asset_name).write_text("abcd1234  other-file.tar.gz\n")

        result = self.run_helper()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Checksum entry", result.stderr)


if __name__ == "__main__":
    unittest.main()
