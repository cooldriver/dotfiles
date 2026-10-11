"""Offline regression checks for shell validation, never deployment."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(all(shutil.which(tool) for tool in ("bash", "zsh", "shellcheck")),
                     "Bash, Zsh and ShellCheck are required")
class ShellValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-check-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.env = dict(os.environ, HOME=str(self.home),
                        XDG_CONFIG_HOME=str(self.home / ".config"),
                        XDG_CACHE_HOME=str(self.home / ".cache"),
                        XDG_DATA_HOME=str(self.home / ".local/share"))
        for name in ("BASH_ENV", "ENV", "ZDOTDIR", "SHELLCHECK_OPTS"):
            self.env.pop(name, None)
        for name in ("bootstrap", "services", "scripts", "shell/.local/bin",
                     "macos/.local/bin", "macos/.config/direnv"):
            (self.base / name).mkdir(parents=True)
        self.script = self.base / "scripts/check-shell.sh"
        shutil.copyfile(ROOT / "scripts/check-shell.sh", self.script)
        self.marker = self.base / "executed"
        for name in ("bootstrap/probe.sh", "shell/.local/bin/helper",
                     "macos/.local/bin/helper", "macos/.config/direnv/direnvrc",
                     "shell/.zshrc", "macos/local.zshrc"):
            (self.base / name).write_text(
                f'#!/usr/bin/env bash\ntouch "{self.marker}"\n'
            )

    def run_check(self, env=None):
        return subprocess.run(["bash", str(self.script)],
                              env=self.env if env is None else env,
                              capture_output=True, text=True)

    def test_hidden_extensionless_and_sourced_files_are_checked_not_executed(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("bootstrap/probe.sh", "shell/.local/bin/helper",
                     "macos/.config/direnv/direnvrc", "shell/.zshrc",
                     "macos/local.zshrc"):
            self.assertIn(name, result.stdout)
        self.assertFalse(self.marker.exists())

    def test_discovery_failure_is_not_reported_as_success(self):
        fake_bin = self.base / "fake-bin"
        fake_bin.mkdir()
        find = fake_bin / "find"
        env = dict(self.env, PATH=f"{fake_bin}:{self.env['PATH']}")
        for failing_root in ("bootstrap", "shell"):
            with self.subTest(failing_root=failing_root):
                find.write_text(
                    f'#!/bin/sh\nif [ "$1" = "{failing_root}" ]; then exit 9; fi\n'
                    f'exec "{shutil.which("find")}" "$@"\n'
                )
                find.chmod(0o755)
                result = self.run_check(env)
                self.assertEqual(result.returncode, 9, result.stderr)
                self.assertFalse(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
