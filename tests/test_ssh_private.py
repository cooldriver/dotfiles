"""Offline SSH backup checks: synthetic data, temporary homes, no credentials."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SSHPrivateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-ssh-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.config = self.home / ".ssh/config.private"
        self.config.parent.mkdir()
        self.config.write_text("Host synthetic.example\n    IdentityFile ~/.ssh/synthetic.pub\n")
        self.archive = self.base / "backup/config.private.age"
        self.recipients = self.base / "recipients.txt"
        self.recipients.write_text("synthetic-public-recipient\n")
        self.bin = self.base / "bin"
        self.bin.mkdir()
        # Deliberately not encryption: exercise process/IO failures separately
        # from the optional real-age round-trip below.
        age = self.bin / "age"
        age.write_text(
            f"#!{sys.executable}\n"
            "import os, pathlib, sys\n"
            "sys.stdout.buffer.write(pathlib.Path(sys.argv[-1]).read_bytes())\n"
            "sys.exit(7 if os.environ.get('FAIL_AGE') else 0)\n"
        )
        age.chmod(0o755)
        self.env = dict(os.environ, HOME=str(self.home), PATH=f"{self.bin}:{os.environ['PATH']}")

    def run_tool(self, action, *extra, env=None, input_text=None):
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts/ssh-private.py"), action,
             "--config", str(self.config), "--archive", str(self.archive),
             "--recipients", str(self.recipients), *extra],
            capture_output=True, text=True, env=self.env if env is None else env,
            input=input_text,
        )

    def test_encrypt_preserves_existing_archive_unless_explicit(self):
        self.assertEqual(self.run_tool("encrypt").returncode, 0)
        first = self.archive.read_bytes()
        self.config.write_text("Host changed.example\n")
        self.assertNotEqual(self.run_tool("encrypt").returncode, 0)
        self.assertEqual(self.archive.read_bytes(), first)
        self.assertEqual(self.run_tool("encrypt", "--replace").returncode, 0)
        self.assertEqual(self.archive.read_bytes(), self.config.read_bytes())
        self.assertEqual(list(self.archive.parent.glob(".ssh-private-*")), [])

    def test_failed_encryption_preserves_archive_and_cleans_temporary(self):
        self.archive.parent.mkdir()
        self.archive.write_bytes(b"previous-ciphertext")
        result = self.run_tool("encrypt", "--replace", env=dict(self.env, FAIL_AGE="1"))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.archive.read_bytes(), b"previous-ciphertext")
        self.assertEqual(list(self.archive.parent.glob(".ssh-private-*")), [])

    def test_restore_is_private_and_never_overwrites(self):
        content = self.config.read_bytes()
        self.assertEqual(self.run_tool("encrypt").returncode, 0)
        self.config.unlink()
        result = self.run_tool("decrypt", "--identity", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config.read_bytes(), content)
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)
        for extra in ([], ["--replace"]):
            self.assertNotEqual(self.run_tool("decrypt", "--identity", "-", *extra).returncode, 0)
            self.assertEqual(self.config.read_bytes(), content)

    def test_failed_decryption_never_publishes_partial_plaintext(self):
        self.assertEqual(self.run_tool("encrypt").returncode, 0)
        self.config.unlink()
        result = self.run_tool("decrypt", "--identity", "-", env=dict(self.env, FAIL_AGE="1"))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.config.exists())
        self.assertEqual(list(self.config.parent.glob(".ssh-private-*")), [])

    def test_rejects_symlinks_and_plaintext_paths_inside_repository(self):
        self.archive.parent.mkdir()
        self.archive.symlink_to(self.base / "absent")
        self.assertNotEqual(self.run_tool("encrypt", "--replace").returncode, 0)
        self.archive.unlink()
        self.config.unlink()
        self.config.symlink_to(self.base / "absent")
        self.assertNotEqual(self.run_tool("decrypt", "--identity", "-").returncode, 0)
        self.config = ROOT / "never-create-plaintext"
        self.assertNotEqual(self.run_tool("encrypt").returncode, 0)
        self.assertFalse(self.config.exists())

    def test_missing_tools_inputs_and_decryption_identity_fail_safely(self):
        result = self.run_tool("encrypt", env=dict(self.env, PATH=str(self.base / "empty")))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("age is required", result.stderr)
        self.recipients.unlink()
        self.assertNotEqual(self.run_tool("encrypt").returncode, 0)
        self.assertNotEqual(self.run_tool("decrypt").returncode, 0)
        self.assertFalse(self.archive.exists())

    @unittest.skipUnless(shutil.which("age") and shutil.which("age-keygen"), "age and age-keygen required for real crypto round-trip")
    def test_real_age_round_trip_and_wrong_identity(self):
        identity = self.base / "identity"
        keygen = subprocess.run(["age-keygen", "-o", str(identity)], capture_output=True, text=True)
        self.assertEqual(keygen.returncode, 0, keygen.stderr)
        public = subprocess.run(["age-keygen", "-y", str(identity)], capture_output=True, text=True, check=True)
        self.recipients.write_text(public.stdout)
        real_env = dict(self.env, PATH=os.environ["PATH"])
        content = self.config.read_bytes()
        encrypted = self.run_tool("encrypt", env=real_env)
        self.assertEqual(encrypted.returncode, 0, encrypted.stderr)
        self.assertNotIn(b"synthetic.example", self.archive.read_bytes())
        self.config.unlink()
        wrong = self.base / "wrong-identity"
        subprocess.run(["age-keygen", "-o", str(wrong)], capture_output=True, check=True)
        self.assertNotEqual(self.run_tool("decrypt", "--identity", str(wrong), env=real_env).returncode, 0)
        self.assertFalse(self.config.exists())
        result = self.run_tool("decrypt", "--identity", str(identity), env=real_env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.config.read_bytes(), content)
        self.config.unlink()
        piped = self.run_tool("decrypt", "--identity", "-", env=real_env, input_text=identity.read_text())
        self.assertEqual(piped.returncode, 0, piped.stderr)
        self.assertEqual(self.config.read_bytes(), content)

    @unittest.skipUnless(shutil.which("stow"), "Stow required")
    def test_stow_keeps_ssh_directory_local_and_preserves_private_config(self):
        original = self.config.read_bytes()
        command = ["stow", "--no-folding", "--dir", str(ROOT), "--target", str(self.home), "ssh"]
        preview = subprocess.run(command + ["--simulate"], capture_output=True, text=True)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.config.parent.is_symlink())
        self.assertTrue((self.config.parent / "config").is_symlink())
        self.assertEqual(self.config.read_bytes(), original)
        self.assertFalse(self.config.is_symlink())

    @unittest.skipUnless(shutil.which("ssh"), "OpenSSH required")
    def test_existing_github_aliases_use_private_key_paths_without_accumulation(self):
        config = self.home / "github-scaffold"
        config.write_text((ROOT / "ssh/.ssh/config").read_text().replace("~/", f"{self.home}/"))
        self.config.write_text(
            f"Host personalgit\n    IdentityFile {self.home}/.ssh/synthetic-personal.pub\n"
            f"Host workgit\n    IdentityFile {self.home}/.ssh/synthetic-work.pub\n"
        )
        for alias, key in (("personalgit", "synthetic-personal"), ("workgit", "synthetic-work")):
            result = subprocess.run(["ssh", "-G", "-F", str(config), alias], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            for expected in ("hostname github.com", "user git", "identitiesonly yes"):
                self.assertIn(expected, lines)
            identities = [line for line in lines if line.startswith("identityfile ")]
            self.assertEqual(identities, [f"identityfile {self.home}/.ssh/{key}.pub"])
            self.assertNotIn("hostkeyalias github.com", lines)

    @unittest.skipUnless(shutil.which("ssh"), "OpenSSH required")
    def test_private_jump_and_target_select_their_own_identities(self):
        config = self.home / "jump-scaffold"
        config.write_text((ROOT / "ssh/.ssh/config").read_text().replace("~/", f"{self.home}/"))
        self.config.write_text(
            "Host bastion.example\n    User jump-user\n    Port 2222\n"
            f"    IdentityFile {self.home}/.ssh/jump.pub\n"
            "Host target-alias\n    HostName 192.0.2.20\n    User target-user\n"
            f"    IdentityFile {self.home}/.ssh/target.pub\n"
            "    ProxyJump bastion.example\n"
            "Host keyless.example\n    PubkeyAuthentication no\n"
        )
        for host, user, key in (("bastion.example", "jump-user", "jump"), ("target-alias", "target-user", "target")):
            result = subprocess.run(["ssh", "-G", "-F", str(config), host], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            self.assertIn("identitiesonly yes", lines)
            self.assertIn(f"user {user}", lines)
            self.assertEqual([line for line in lines if line.startswith("identityfile ")],
                             [f"identityfile {self.home}/.ssh/{key}.pub"])
            if host == "bastion.example":
                self.assertIn("port 2222", lines)
                self.assertFalse(any(line.startswith("proxyjump ") for line in lines))
            else:
                self.assertIn("hostname 192.0.2.20", lines)
                self.assertIn("proxyjump bastion.example", lines)
        result = subprocess.run(["ssh", "-G", "-F", str(config), "keyless.example"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pubkeyauthentication false", result.stdout.splitlines())

    @unittest.skipUnless(shutil.which("ssh"), "OpenSSH required")
    def test_specific_identity_and_orbstack_survive_public_defaults(self):
        # OpenSSH expands ~ using the account database, not an isolated HOME.
        # Rewrite every tilde path into this temporary home before invoking it.
        config = self.home / "scaffold"
        config.write_text((ROOT / "ssh/.ssh/config").read_text().replace("~/", f"{self.home}/"))
        self.config.write_text(
            f"Host synthetic.example 192.0.2.10\n    User test-user\n"
            f"    IdentityFile {self.home}/.ssh/synthetic.pub\n"
        )
        orb = self.home / ".orbstack/ssh"
        orb.mkdir(parents=True)
        (orb / "config").write_text(
            "Host orb\n    HostName 127.0.0.1\n    Port 32222\n    User orb-user\n"
            f"    IdentityFile {orb}/synthetic-key\n"
            f"    UserKnownHostsFile {orb}/known_hosts\n"
            "    ProxyCommand /synthetic/orbstack-helper ssh-proxy\n"
            "    IdentityAgent none\n    IdentitiesOnly no\n"
        )
        for host, expected in (("synthetic.example", "user test-user"), ("192.0.2.10", "user test-user"), ("orb", "user orb-user")):
            result = subprocess.run(["ssh", "-G", "-F", str(config), host], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(expected, result.stdout)
            if host == "orb":
                self.assertIn("identityagent none", result.stdout)
                self.assertIn("identitiesonly no", result.stdout)
                lines = result.stdout.splitlines()
                for expected in ("hostname 127.0.0.1", "port 32222",
                                 f"userknownhostsfile {orb}/known_hosts",
                                 "proxycommand /synthetic/orbstack-helper ssh-proxy"):
                    self.assertIn(expected, lines)
                self.assertEqual([line for line in lines if line.startswith("identityfile ")],
                                 [f"identityfile {orb}/synthetic-key"])
            else:
                self.assertIn("identitiesonly yes", result.stdout)
                self.assertIn(f"identityfile {self.home}/.ssh/synthetic.pub", result.stdout)
                self.assertIn(f"identityagent {self.home}/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock",
                              result.stdout.splitlines())


if __name__ == "__main__":
    unittest.main()
