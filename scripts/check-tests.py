"""Run offline tests without the Git-mutating identity test (agent policy)."""

from pathlib import Path
import sys
import unittest


EXCLUDED = "test_macos.MacOSPreparationTests.test_git_personal_identity_is_default_and_work_overrides_it"


def permitted_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from permitted_tests(item)
        elif item.id() == EXCLUDED:
            print(f"EXCLUDED (Git policy): {item.id()}", flush=True)
        else:
            yield item


def main():
    root = Path(__file__).resolve().parents[1]
    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.TestSuite(permitted_tests(suite))
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
