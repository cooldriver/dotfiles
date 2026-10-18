"""Offline standalone installer tests, with synthetic downloads and temporary HOME."""

import os
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "bootstrap/linux/install-atuin.sh"


@unittest.skipUnless(shutil.which("bash"), "Bash required")
class AtuinInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-atuin-install-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.log = self.base / "calls"
        self.env = dict(os.environ, HOME=str(self.home), TMPDIR=str(self.base),
                        XDG_CONFIG_HOME=str(self.home / "xdg"), TEST_LOG=str(self.log),
                        PATH=f"{self.bin}:{os.environ['PATH']}")
        for key in ("BASH_ENV", "ENV"):
            self.env.pop(key, None)
        self.fake("uname", '''
case "$1" in
  -s) printf '%s\\n' "${TEST_OS:-Linux}" ;;
  -m) printf '%s\\n' "${TEST_ARCH:-x86_64}" ;;
esac
''')
        self.fake("curl", '''
printf 'download:%s\\n' "$*" >> "$TEST_LOG"
[ "${FAIL_DOWNLOAD:-0}" = 0 ] || exit 7
while [ "$1" != --output ]; do shift; done
cp "$TEST_INSTALLER" "$2"
''')
        self.fake("sha256sum", '''
printf 'checksum:%s\\n' "$*" >> "$TEST_LOG"
cat >> "$TEST_LOG"
[ "${FAIL_CHECKSUM:-0}" = 0 ]
''')
        installer = self.base / "fake-installer.sh"
        installer.write_text('''#!/bin/sh
set -eu
printf 'install:%s:%s\\n' "$ATUIN_INSTALL_DIR" "$ATUIN_NO_MODIFY_PATH" >> "$TEST_LOG"
[ "${FAIL_INSTALL:-0}" = 0 ] || exit 9
mkdir -p "$ATUIN_INSTALL_DIR" "$XDG_CONFIG_HOME/atuin"
printf '#!/bin/sh\\nprintf "atuin 18.24.1\\\\n"\\n' > "$ATUIN_INSTALL_DIR/atuin"
chmod 755 "$ATUIN_INSTALL_DIR/atuin"
python3 - <<'PY'
import json
import os
from pathlib import Path
receipt = {
    "version": "18.24.1", "install_prefix": os.environ["ATUIN_INSTALL_DIR"],
    "install_layout": "flat", "binaries": ["atuin"], "modify_path": False,
    "source": {"app_name": "atuin", "name": "atuin", "owner": "atuinsh", "release_type": "github"},
    "provider": {"source": "cargo-dist", "version": "0.31.0"},
}
(Path(os.environ["XDG_CONFIG_HOME"]) / "atuin/atuin-receipt.json").write_text(json.dumps(receipt))
PY
''')
        self.env["TEST_INSTALLER"] = str(installer)
        (self.home / ".zshrc").write_text("# existing shell\n")
        self.data = self.home / ".local/share/atuin"
        self.data.mkdir(parents=True)
        (self.data / "key").write_text("synthetic-key\n")
        (self.data / "history.db").write_bytes(b"synthetic database")

    def fake(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\nset -eu\n" + body)
        path.chmod(0o755)

    def run_installer(self):
        return subprocess.run(["bash", str(SCRIPT)], env=self.env,
                              capture_output=True, text=True)

    def assert_personal_files_preserved(self):
        self.assertEqual((self.home / ".zshrc").read_text(), "# existing shell\n")
        self.assertEqual((self.data / "key").read_text(), "synthetic-key\n")
        self.assertEqual((self.data / "history.db").read_bytes(), b"synthetic database")

    def test_verified_official_installer_preserves_shell_and_data(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text()
        self.assertIn("https://github.com/atuinsh/atuin/releases/download/v18.24.1/atuin-installer.sh", calls)
        self.assertIn("69c7c0e057084ede4536de25f856c037f4649dcf8f29cc98a64ac52340320a99", calls)
        self.assertLess(calls.index("checksum:"), calls.index("install:"))
        self.assertIn(f"install:{self.home}/.atuin/bin:1", calls)
        self.assertTrue((self.home / ".atuin/bin/atuin").is_file())
        self.assert_personal_files_preserved()

    def test_rerun_keeps_existing_client_without_downgrade_or_network(self):
        self.assertEqual(self.run_installer().returncode, 0)
        binary = self.home / ".atuin/bin/atuin"
        binary.write_text('#!/bin/sh\n# newer installation\nprintf "atuin 19.0.0\\n"\n')
        calls = self.log.read_text()
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("newer installation", binary.read_text())
        self.assertEqual(self.log.read_text(), calls)
        self.assert_personal_files_preserved()

    def test_checksum_failure_never_executes_download(self):
        self.env["FAIL_CHECKSUM"] = "1"
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("install:", self.log.read_text())
        self.assertFalse((self.home / ".atuin").exists())
        self.assert_personal_files_preserved()

    def test_download_failure_never_executes_installer(self):
        self.env["FAIL_DOWNLOAD"] = "1"
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("install:", self.log.read_text())
        self.assert_personal_files_preserved()

    def test_installer_failure_is_reported(self):
        self.env["FAIL_INSTALL"] = "1"
        self.assertEqual(self.run_installer().returncode, 9)
        self.assert_personal_files_preserved()

    def test_partial_or_unmanaged_installation_is_not_overwritten(self):
        directory = self.home / ".atuin"
        directory.mkdir()
        marker = directory / "keep"
        marker.write_text("keep")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())
        self.assertEqual(marker.read_text(), "keep")

    def test_old_standalone_requires_explicit_update_without_overwrite(self):
        self.assertEqual(self.run_installer().returncode, 0)
        binary = self.home / ".atuin/bin/atuin"
        content = '#!/bin/sh\nprintf "atuin 18.6.1\\n"\n'
        binary.write_text(content)
        calls = self.log.read_text()
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("update", result.stderr)
        self.assertEqual(binary.read_text(), content)
        self.assertEqual(self.log.read_text(), calls)

    def test_broken_symlink_is_not_replaced(self):
        (self.home / ".atuin").symlink_to(self.base / "missing")
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.home / ".atuin").is_symlink())
        self.assertFalse(self.log.exists())

    def test_empty_truncated_and_mismatched_receipts_are_rejected(self):
        self.assertEqual(self.run_installer().returncode, 0)
        receipt = Path(self.env["XDG_CONFIG_HOME"]) / "atuin/atuin-receipt.json"
        valid = json.loads(receipt.read_text())
        wrong_prefix = dict(valid, install_prefix=str(self.base / "other"))
        wrong_source = dict(valid, source=dict(valid["source"], owner="other"))
        calls = self.log.read_text()
        for content in ("", '{"source":', "{}", "[]", json.dumps(wrong_prefix), json.dumps(wrong_source)):
            with self.subTest(content=content):
                receipt.write_text(content)
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("receipt", result.stderr)
                self.assertEqual(receipt.read_text(), content)
                self.assertEqual(self.log.read_text(), calls)

    def test_unsupported_platform_stops_before_download(self):
        for key, value in (("TEST_OS", "Darwin"), ("TEST_ARCH", "armv7l")):
            with self.subTest(key=key):
                self.env[key] = value
                self.assertNotEqual(self.run_installer().returncode, 0)
                self.assertFalse(self.log.exists())
                del self.env[key]
