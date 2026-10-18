"""Offline btop configuration contracts; no real btop or home deployment."""

from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BtopTests(unittest.TestCase):
    def test_generated_reference_preserves_shared_preferences(self):
        config = (ROOT / "btop/.config/btop/btop.conf").read_text()
        self.assertTrue(config.startswith("#? Config file for btop v. 1.3.2\n"))
        settings = dict(
            line.split(" = ", 1)
            for line in config.splitlines()
            if line and not line.startswith("#")
        )
        expected = {
            "color_theme": '"Default"',
            "truecolor": "True",
            "rounded_corners": "True",
            "graph_symbol": '"braille"',
            "update_ms": "2000",
            "proc_mem_bytes": "True",
            "temp_scale": '"celsius"',
            "show_disks": "True",
            "show_swap": "True",
        }
        for key, value in expected.items():
            self.assertEqual(settings[key], value, key)
        self.assertNotIn("save_config_on_exit", settings)

    @unittest.skipUnless(shutil.which("git"), "Git is needed to check ignore rules")
    def test_only_exact_btop_log_is_ignored(self):
        candidates = [
            "btop/.config/btop/btop.log",
            "btop/.config/btop/btop.conf",
            "btop/.config/btop/other.log",
            "btop/.config/btop/btop.log.1",
            "shell/.config/btop/btop.log",
        ]
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--stdin"],
            cwd=ROOT, input="\n".join(candidates) + "\n",
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), candidates[:1])


if __name__ == "__main__":
    unittest.main()
