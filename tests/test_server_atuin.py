"""Explicit server opt-in with temporary Stow homes and a fake Atuin command."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("stow") and shutil.which("zsh"), "Stow and Zsh required")
class ServerAtuinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-server-atuin-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.log = self.base / "init-config"
        self.env = dict(HOME=str(self.home), PATH=str(self.bin), TERM="dumb",
                        TEST_LOG=str(self.log), ATUIN_AUTO_SYNC="false",
                        ATUIN_SYNC_FREQUENCY="1h")
        self.fake("hostname", "printf 'test-server\\n'")
        self.fake("atuin", '''
[ "$*" = 'init zsh --disable-up-arrow' ] || exit 2
printf '%s\\n' "${ATUIN_CONFIG_DIR:-manual}" > "$TEST_LOG"
''')
        self.stow("--stow", "shell")

    def fake(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)

    def stow(self, action, *packages):
        result = subprocess.run(
            [shutil.which("stow"), action, "--dir", str(ROOT),
             "--target", str(self.home), *packages],
            env=dict(os.environ, HOME=str(self.home)), capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def shell(self):
        result = subprocess.run(
            [shutil.which("zsh"), "-f", "-i", "-c",
             'source "$HOME/.zshrc"; print -r -- "${ATUIN_CONFIG_DIR:-manual}"'],
            env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_shared_shell_stays_manual_without_server_package(self):
        self.assertEqual(self.shell(), "manual")
        self.assertEqual(self.log.read_text().strip(), "manual")
        config = tomllib.loads((self.home / ".config/atuin/config.toml").read_text())
        self.assertFalse(config["auto_sync"])

    def test_server_profile_selected_before_init_and_removal_restores_manual(self):
        self.stow("--stow", "linux-server")
        expected = str(self.home / ".config/atuin/profiles/linux-server")
        self.assertEqual(self.shell(), expected)
        self.assertEqual(self.log.read_text().strip(), expected)
        config = tomllib.loads((Path(expected) / "config.toml").read_text())
        self.assertEqual(config["sync_address"], "https://atuin.hwapp.ovh")
        self.assertTrue(config["auto_sync"])
        self.assertEqual(config["sync_frequency"], "5m")
        self.assertFalse(config["daemon"]["enabled"])
        self.assertFalse(config["update_check"])
        self.stow("--delete", "linux-server")
        self.assertEqual(self.shell(), "manual")

    def test_xdg_config_home_is_respected(self):
        self.stow("--stow", "linux-server")
        custom = self.home / "custom-config"
        (self.home / ".config").rename(custom)
        self.env["XDG_CONFIG_HOME"] = str(custom)
        expected = str(custom / "atuin/profiles/linux-server")
        self.assertEqual(self.shell(), expected)
        self.assertEqual(self.log.read_text().strip(), expected)

    def test_local_override_is_preserved(self):
        self.stow("--stow", "linux-server")
        local = self.home / ".config/zsh/local.zsh"
        local.write_text('export ATUIN_CONFIG_DIR="$HOME/.config/atuin"\n')
        self.assertEqual(self.shell(), str(self.home / ".config/atuin"))
        self.assertTrue(local.is_file())
