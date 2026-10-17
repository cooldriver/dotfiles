"""Explicit age encryption/restoration; never deploy into HOME implicitly."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def outside_repository(path):
    if path.resolve().is_relative_to(ROOT):
        raise ValueError("Plaintext configuration and private identity must stay outside the repository")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("encrypt", "decrypt"))
    parser.add_argument("--config", type=Path, default=Path.home() / ".ssh/config.private")
    parser.add_argument("--archive", type=Path, default=ROOT / "private/ssh/config.private.age")
    parser.add_argument("--recipients", type=Path, default=ROOT / "private/ssh/recipients.txt")
    parser.add_argument("--identity", help="Decryption identity outside the repository; '-' reads from stdin")
    parser.add_argument("--replace", action="store_true", help="Explicitly replace existing ciphertext (encrypt only)")
    args = parser.parse_args()
    temporary = None
    try:
        outside_repository(args.config)
        if args.config.is_symlink() or args.archive.is_symlink():
            raise ValueError("Configuration and archive must not be symlinks")
        if not shutil.which("age"):
            raise ValueError("age is required; install it before running this command")
        if args.action == "encrypt":
            if args.identity:
                raise ValueError("--identity is only used for decryption")
            if not args.config.is_file() or not args.recipients.is_file():
                raise ValueError("Configuration and public recipients file must exist")
            source, destination = args.config, args.archive
            command = ["age", "--encrypt", "--recipients-file", str(args.recipients), str(source)]
        else:
            if args.replace:
                raise ValueError("Restoration never replaces existing files; --replace is encrypt-only")
            if not args.identity or not args.archive.is_file():
                raise ValueError("Decryption requires --identity and an existing archive")
            if args.identity != "-":
                outside_repository(Path(args.identity))
            source, destination = args.archive, args.config
            command = ["age", "--decrypt", "--identity", args.identity, str(source)]
        if destination.exists() and not args.replace:
            raise ValueError("Destination exists; preserve it or explicitly replace ciphertext with --replace")
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".ssh-private-", dir=destination.parent)
        # mkstemp creates a private 0600 file, including while decrypting.
        with os.fdopen(fd, "wb") as output:
            subprocess.run(command, stdout=output, check=True)
            output.flush()
            os.fsync(output.fileno())
        if args.replace:
            os.replace(temporary, destination)
        else:
            # Atomic no-clobber publication, even if another process created it.
            os.link(temporary, destination)
        print("Encrypted archive saved." if args.action == "encrypt" else "Private configuration restored (0600).")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"SSH private configuration: {error}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
