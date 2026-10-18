"""btop stays installed, but its configuration is no longer managed here."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BtopTests(unittest.TestCase):
    def test_no_shared_btop_configuration(self):
        self.assertFalse((ROOT / "btop/.config/btop/btop.conf").exists())

    def test_homebrew_still_installs_btop(self):
        self.assertRegex(
            (ROOT / "brew/Brewfile").read_text(), r"(?m)^brew ['\"]btop['\"]\s"
        )


if __name__ == "__main__":
    unittest.main()
