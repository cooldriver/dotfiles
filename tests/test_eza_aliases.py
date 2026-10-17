"""Offline checks for optional eza shortcuts in an isolated Zsh."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ALIASES = ROOT / "shell/.config/zsh/aliases.zsh"
COMMON = ["--color=always", "--icons=always"]


@unittest.skipUnless(shutil.which("zsh"), "Zsh is required")
class EzaAliasTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-eza-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.home),
                        XDG_CONFIG_HOME=str(self.home / ".config"),
                        XDG_CACHE_HOME=str(self.home / ".cache"),
                        XDG_DATA_HOME=str(self.home / ".local/share"),
                        PATH=str(self.bin))
        for name in ("ZDOTDIR", "ENV", "BASH_ENV"):
            self.env.pop(name, None)
        self.zsh = shutil.which("zsh")

    def run_zsh(self, code):
        result = subprocess.run(
            # Parse commands after sourcing, as a terminal does for the next prompt.
            [self.zsh, "-f", "-c", 'source "$1"; eval "$2"',
             "test", str(ALIASES), code],
            env=self.env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_shortcuts_preserve_paths_and_extra_options(self):
        # A shell function records arguments; the executable makes eza discoverable.
        fake = self.bin / "eza"
        fake.write_text("#!/bin/sh\nexit 0\n")
        fake.chmod(0o755)
        views = {
            "lz": [],
            "lzl": ["--long", "--header", "--group-directories-first",
                    "--color-scale=size", "--octal-permissions"],
            "lzr": ["--long", "--header", "--sort=modified", "--reverse",
                    "--time-style=relative", "--color-scale=age"],
            "lzg": ["--long", "--header", "--all", "--git",
                    "--group-directories-first"],
            "lzt": ["--tree", "--level=2"],
        }
        for alias, options in views.items():
            with self.subTest(alias=alias):
                output = self.run_zsh(
                    'function eza { printf "%s\\0" "$@"; }\n'
                    f'{alias} --level=3 "folder with spaces"\n'
                )
                self.assertEqual(output.split("\0")[:-1],
                                 COMMON + options + ["--level=3", "folder with spaces"])

    def test_shortcuts_are_absent_without_eza(self):
        output = self.run_zsh(
            'for name in lz lzl lzr lzg lzt lat lzs; do\n'
            '  if (( ${+aliases[$name]} )); then print -r -- "$name"; fi\n'
            'done\ntrue\n'
        )
        self.assertEqual(output, "")

    @unittest.skipUnless(shutil.which("eza"), "eza is required for rendering checks")
    def test_real_eza_sorting_and_tree_depth(self):
        (self.bin / "eza").symlink_to(shutil.which("eza"))
        fixture = self.base / "listing"
        fixture.mkdir()
        old_dir = fixture / "a-directory"
        old_dir.mkdir()
        (old_dir / "child").mkdir()
        (old_dir / "child/grandchild").write_text("")
        old_file = fixture / "b-old.txt"
        old_file.write_text("")
        new_file = fixture / "c-new.txt"
        new_file.write_text("")
        for path, timestamp in ((old_dir, 1000000000), (old_file, 1000000010),
                                (new_file, 1000000020)):
            os.utime(path, (timestamp, timestamp))
        # Disable terminal escapes only in these assertions, using eza's overrides.
        path = json.dumps(str(fixture))
        plain = "--color=never --icons=never --hyperlink=never"
        recent = self.run_zsh(f"lzr {plain} {path}\n")
        self.assertLess(recent.index("c-new.txt"), recent.index("b-old.txt"))
        self.assertLess(recent.index("b-old.txt"), recent.index("a-directory"))
        long_view = self.run_zsh(f"lzl {plain} {path}\n")
        self.assertLess(long_view.index("a-directory"), long_view.index("b-old.txt"))
        tree = self.run_zsh(f"lzt {plain} {path}\n")
        self.assertIn("child", tree)
        self.assertNotIn("grandchild", tree)
        deeper = self.run_zsh(f"lzt {plain} --level=3 {path}\n")
        self.assertIn("grandchild", deeper)


if __name__ == "__main__":
    unittest.main()
