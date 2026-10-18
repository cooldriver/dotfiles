"""Offline Zellij installer checks with temporary homes and synthetic downloads."""

import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bootstrap/linux/install-zellij.sh"
# Archive digests checked against the v0.45.1 GitHub assets, not binary manifests.
ARCHIVE_HASHES = {
    "x86_64": "40bcc2e03f5d5ae8e054e39f676081fe12ab70871506996ba595834c3718eefc",
    "aarch64": "05f0802afadd53f8db9514e7cae53c9ae8432fed1b35b8294aa816ee3044a16b",
}


@unittest.skipUnless(shutil.which("bash") and shutil.which("tar"), "Bash and tar required")
class ZellijInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-zellij-install-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.log = self.base / "calls"
        self.link = self.home / ".local/bin/zellij"
        self.target = self.home / ".local/opt/zellij/v0.45.1/zellij"
        self.env = dict(os.environ, HOME=str(self.home), TMPDIR=str(self.base),
                        TEST_LOG=str(self.log), TEST_ARCH="x86_64",
                        TEST_EXPECTED_CHECKSUM=ARCHIVE_HASHES["x86_64"],
                        PATH=f"{self.bin}:{os.environ['PATH']}")
        for key in ("BASH_ENV", "ENV"):
            self.env.pop(key, None)
        self.fake("uname", '''
case "$1" in
  -s) printf '%s\\n' "${TEST_OS:-Linux}" ;;
  -m) printf '%s\\n' "$TEST_ARCH" ;;
esac
''')
        archive = self.base / "fixture.tar.gz"
        binary = b'#!/bin/sh\nprintf "executed\\n" >> "$TEST_LOG"\nprintf "zellij 0.45.1\\n"\n'
        with tarfile.open(archive, "w:gz") as bundle:
            member = tarfile.TarInfo("zellij")
            member.size = len(binary)
            member.mode = 0o755
            bundle.addfile(member, io.BytesIO(binary))
        self.env["TEST_ARCHIVE"] = str(archive)
        self.fake("curl", '''
printf 'download:%s\\n' "$*" >> "$TEST_LOG"
[ "${FAIL_DOWNLOAD:-0}" = 0 ] || exit 7
while [ "$1" != --output ]; do shift; done
cp "$TEST_ARCHIVE" "$2"
''')
        self.fake("sha256sum", '''
read -r checksum archive
printf 'checksum:%s:%s\\n' "$checksum" "$archive" >> "$TEST_LOG"
[ "${FAIL_CHECKSUM:-0}" = 0 ] || exit 1
[ "$checksum" = "$TEST_EXPECTED_CHECKSUM" ]
''')
        self.config = self.home / ".config/zellij/config.kdl"
        self.config.parent.mkdir(parents=True)
        self.config.write_text("// existing configuration\n")

    def fake(self, name, body):
        file_path = self.bin / name
        file_path.write_text("#!/bin/sh\nset -eu\n" + body)
        file_path.chmod(0o755)

    def run_installer(self):
        return subprocess.run(["bash", str(SCRIPT)], env=self.env,
                              capture_output=True, text=True)

    def test_verified_archive_for_each_architecture_installs_before_execution(self):
        for arch, checksum in ARCHIVE_HASHES.items():
            with self.subTest(arch=arch):
                self.env.update(TEST_ARCH=arch, TEST_EXPECTED_CHECKSUM=checksum)
                result = self.run_installer()
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = self.log.read_text()
                self.assertIn(f"zellij-{arch}-unknown-linux-musl.tar.gz", calls)
                self.assertIn(f"checksum:{checksum}:", calls)
                self.assertLess(calls.index("checksum:"), calls.index("executed"))
                self.assertEqual(os.readlink(self.link), str(self.target))
                self.assertIn("zellij 0.45.1", result.stdout)
                self.assertEqual(self.config.read_text(), "// existing configuration\n")
                self.link.unlink()
                self.target.unlink()
                self.log.unlink()

    def test_checksum_failure_is_explicit_and_preserves_old_version(self):
        previous = self.home / ".local/opt/zellij/v0.44.0/zellij"
        previous.parent.mkdir(parents=True)
        previous.write_text("existing version\n")
        previous.chmod(0o755)
        self.link.parent.mkdir(parents=True)
        self.link.symlink_to(previous)
        self.env["FAIL_CHECKSUM"] = "1"
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)
        self.assertIn("zellij-x86_64-unknown-linux-musl.tar.gz", result.stderr)
        self.assertNotIn("executed", self.log.read_text())
        self.assertFalse(self.target.parent.exists())
        self.assertEqual(os.readlink(self.link), str(previous))
        self.assertEqual(previous.read_text(), "existing version\n")
        self.assertEqual(self.config.read_text(), "// existing configuration\n")

    def test_rerun_uses_existing_version_without_download(self):
        self.assertEqual(self.run_installer().returncode, 0)
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().count("download:"), 1)
        self.assertEqual(self.log.read_text().count("checksum:"), 1)
        self.assertEqual(self.log.read_text().count("executed"), 2)

    def test_download_failure_does_not_install_or_repoint(self):
        self.env["FAIL_DOWNLOAD"] = "1"
        result = self.run_installer()
        self.assertEqual(result.returncode, 7)
        self.assertNotIn("checksum:", self.log.read_text())
        self.assertNotIn("executed", self.log.read_text())
        self.assertFalse(self.target.exists())
        self.assertFalse(self.link.is_symlink())

    def test_unmanaged_binary_is_not_overwritten(self):
        self.link.parent.mkdir(parents=True)
        self.link.write_text("unmanaged\n")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unmanaged", result.stderr)
        self.assertEqual(self.link.read_text(), "unmanaged\n")
        self.assertFalse(self.log.exists())

    def test_unsupported_platform_stops_before_download(self):
        for key, value in (("TEST_OS", "Darwin"), ("TEST_ARCH", "armv7l")):
            with self.subTest(key=key):
                original = self.env.get(key)
                self.env[key] = value
                self.assertNotEqual(self.run_installer().returncode, 0)
                self.assertFalse(self.log.exists())
                if original is None:
                    del self.env[key]
                else:
                    self.env[key] = original
