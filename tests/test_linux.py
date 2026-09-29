"""Offline Linux bootstrap checks: no APT, network, or real home changes."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "bootstrap/linux/common.sh"


@unittest.skipUnless(shutil.which("bash"), "Bash is needed for the bootstrap tests")
class LinuxBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dotfiles-linux-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.log = self.base / "calls"
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.home), TEST_LOG=str(self.log))

    def run_bootstrap_functions(self, script):
        return subprocess.run(
            ["bash", "-c", 'source "$1"\n' + script, "bash", str(COMMON)],
            env=self.env, capture_output=True, text=True,
        )

    def test_common_packages_require_delta_and_keep_lazygit_optional(self):
        result = self.run_bootstrap_functions('''
install_required() { printf 'required:%s\\n' "$*" >> "$TEST_LOG"; }
install_optional() { printf 'optional:%s\\n' "$*" >> "$TEST_LOG"; }
bash() { printf 'installer:%s\\n' "$*" >> "$TEST_LOG"; }
install_common_packages
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        required, optional, installer = self.log.read_text().splitlines()
        self.assertIn("git-delta", required.split())
        self.assertIn("lazygit", optional.split())
        self.assertNotIn("lazygit", required.split())
        self.assertNotIn("git-delta", optional.split())
        self.assertIn("install-zellij.sh", installer)

    def test_optional_packages_skip_unavailable_ones(self):
        result = self.run_bootstrap_functions('''
apt-cache() { [[ "$2" != lazygit ]]; }
run_privileged() { printf '%s\\n' "$*" >> "$TEST_LOG"; }
install_optional lazygit ripgrep
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), ["apt-get install --yes ripgrep"])
        self.assertIn("Skipping unavailable optional package: lazygit", result.stderr)

    def test_shell_dependencies_keep_existing_clones_and_theme(self):
        result = self.run_bootstrap_functions('''
git() {
  printf '%s\\n' "$*" >> "$TEST_LOG"
  mkdir -p "$4"
}
install_shell_dependencies
install_shell_dependencies
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.log.read_text().splitlines()), 2)
        theme = self.home / ".oh-my-zsh/custom/themes/spaceship.zsh-theme"
        self.assertTrue(theme.is_symlink())
        self.assertEqual(os.readlink(theme), "spaceship-prompt/spaceship.zsh-theme")


if __name__ == "__main__":
    unittest.main()
