"""Offline checks for PATH inspection without loading personal shell files."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("zsh") and shutil.which("sort"),
                     "Zsh and sort are required")
class PathHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-path-test-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        home = base / "home"
        home.mkdir()
        bin_dir = base / "bin"
        bin_dir.mkdir()
        (bin_dir / "sort").symlink_to(shutil.which("sort"))
        self.entries = [str(base / "z-last"), str(base / "a space"),
                        str(base / "z-last"), str(bin_dir)]
        self.env = dict(HOME=str(home), PATH=os.pathsep.join(self.entries),
                        XDG_CONFIG_HOME=str(home / ".config"), LC_ALL="C")

    def run_helper(self, *args):
        return subprocess.run(
            [shutil.which("zsh"), "-f", "-c", 'source "$1"; hpath "${@:2}"',
             "test", str(ROOT / "shell/.config/zsh/aliases.zsh"), *args],
            env=self.env, capture_output=True, text=True,
        )

    def test_default_is_alphabetical_and_preserves_duplicates_and_spaces(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = sorted(enumerate(self.entries, 1), key=lambda item: item[1])
        self.assertEqual(result.stdout.splitlines(),
                         [f"{index:3d}\t{entry}" for index, entry in expected])

    def test_ordered_preserves_search_order(self):
        result = self.run_helper("--ordered")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         [f"{index:3d}\t{entry}"
                          for index, entry in enumerate(self.entries, 1)])

    def test_invalid_arguments_fail_without_a_listing(self):
        for args in (("--unknown",), ("--ordered", "extra"), ("",)):
            with self.subTest(args=args):
                result = self.run_helper(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "Usage: hpath [--ordered]\n")


if __name__ == "__main__":
    unittest.main()
