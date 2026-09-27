"""Offline tests: no network, launchctl, credentials, or installed services."""

from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "services/macos/toola-atuin-sync.sh"
PLIST = ROOT / "services/macos/com.fieldbook.toola-atuin-sync.plist"


class ToolaAtuinSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="toola-atuin-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.home = self.base / "home"
        (self.home / ".config/atuin").mkdir(parents=True)
        (self.home / ".config/atuin/config.toml").write_text("auto_sync = false\n")
        self.env = {
            "HOME": str(self.home),
            "PATH": f"{self.bin}:/usr/bin:/bin:/usr/sbin:/sbin",
            "TEST_ROOT": str(self.base),
            "TEST_HOST": "Toola",
            "TEST_IP": "10.0.1.35",
            "TEST_DNS": "10.0.30.100",
            "TEST_CURL_STATUS": "0",
        }
        self.fake("hostname", 'printf "%s\\n" "$TEST_HOST"')
        self.fake("ifconfig", 'printf "en0 en1 utun3\\n"')
        self.fake("ipconfig", '[[ "$2" == en0 ]] || exit 1; printf "%s\\n" "$TEST_IP"')
        self.fake("dscacheutil", 'printf "ip_address: %s\\n" "$TEST_DNS"')
        self.fake("curl", 'printf "%s\\n" "$*" >> "$TEST_ROOT/curl-calls"; exit "$TEST_CURL_STATUS"')
        self.fake("atuin", '''
[[ "$1" == sync ]]
[[ "$ATUIN_CONFIG_DIR" == "$HOME/.config/atuin" ]]
printf "synced\\n" >> "$TEST_ROOT/atuin-calls"
''')

    def fake(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\nset -eu\n" + body + "\n")
        path.chmod(0o755)

    def run_sync(self):
        return subprocess.run(["/bin/bash", str(SCRIPT)], env=self.env,
                              text=True, capture_output=True)

    def assert_no_network(self):
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.base / "curl-calls").exists())
        self.assertFalse((self.base / "atuin-calls").exists())

    def test_requires_toola_and_home_lan(self):
        for change in ({"TEST_HOST": "Tatooine"}, {"TEST_IP": "10.0.1.99"}):
            self.env.update(change)
            self.assert_no_network()
            self.env.update(TEST_HOST="Toola", TEST_IP="10.0.1.35")

    def test_public_or_mixed_dns_skips_even_on_home_address(self):
        for dns in ("193.70.33.182", "10.0.30.100\nip_address: 193.70.33.182"):
            self.env["TEST_DNS"] = dns
            self.assert_no_network()

    def test_private_probe_failure_skips_sync(self):
        self.env["TEST_CURL_STATUS"] = "22"
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.base / "curl-calls").exists())
        self.assertFalse((self.base / "atuin-calls").exists())

    def test_lan_success_pins_private_ip_and_syncs_once(self):
        for local_ip in ("10.0.1.34", "10.0.1.35"):
            self.env["TEST_IP"] = local_ip
            result = self.run_sync()
            self.assertEqual(result.returncode, 0, result.stderr)
        probes = (self.base / "curl-calls").read_text().splitlines()
        self.assertEqual(len(probes), 2)
        for probe in probes:
            self.assertIn("--resolve atuin.hwapp.ovh:443:10.0.30.100", probe)
            self.assertIn("--max-time 8", probe)
        self.assertEqual((self.base / "atuin-calls").read_text(), "synced\nsynced\n")

    def test_agent_is_not_loaded_by_shared_stow(self):
        with PLIST.open("rb") as source:
            agent = plistlib.load(source)
        self.assertEqual(agent["Label"], "com.fieldbook.toola-atuin-sync")
        self.assertEqual(agent["StartInterval"], 300)
        self.assertNotIn("RunAtLoad", agent)
        self.assertNotIn("KeepAlive", agent)
        self.assertFalse((ROOT / "macos/Library/LaunchAgents").exists())


if __name__ == "__main__":
    unittest.main()
