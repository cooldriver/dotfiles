"""Offline behavior checks: no real credentials, deployment, or containers."""

import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MacOSPreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dotfiles-test-")
        self.addCleanup(self.tmp.cleanup)
        # direnv records approvals by path; macOS /var aliases /private/var.
        self.base = Path(self.tmp.name).resolve()
        self.home = self.base / "home"
        self.bin = self.base / "bin"
        self.home.mkdir()
        self.bin.mkdir()
        self.env = os.environ.copy()
        # Never forward real tokens or credential paths to the fake commands.
        for name in list(self.env):
            if name.startswith(("GH_", "GITHUB_", "DIRENV_", "XDG_", "AWS_")):
                del self.env[name]
        self.env.update(
            HOME=str(self.home),
            XDG_CONFIG_HOME=str(self.home / ".config"),
            XDG_DATA_HOME=str(self.home / ".local/share"),
            XDG_CACHE_HOME=str(self.home / ".cache"),
            PATH=f"{self.bin}:{ROOT / 'shell/.local/bin'}:{os.environ['PATH']}",
            TEST_ROOT=str(self.base),
        )

    def fake(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/bash\nset -eu\n" + body + "\n")
        path.chmod(0o755)
        return path

    def run_command(self, args, **kwargs):
        return subprocess.run(
            [str(arg) for arg in args], env=self.env, capture_output=True,
            text=True, **kwargs
        )

    def mock_gh(self):
        self.fake("gh", '''
if [[ "$1 $2" == "auth token" ]]; then
  [[ $# == 6 && "$3" == --hostname && "$4" == github.com && "$5" == --user ]]
  [[ -z "${GH_TOKEN:-}${GITHUB_TOKEN:-}${GH_ENTERPRISE_TOKEN:-}${GITHUB_ENTERPRISE_TOKEN:-}" ]]
  [[ "${GH_HOST:-}" == github.com ]]
  [[ "$6" != missing ]] || exit 17
  [[ "$6" != empty ]] || exit 0
  printf 'test-token-%s' "$6"
else
  [[ "${GH_HOST:-}" == github.com ]]
  printf '%s\\n' "${GH_TOKEN#test-token-}" "$@"
fi
''')

    def test_github_accounts_are_process_local_and_arguments_survive(self):
        self.mock_gh()
        self.env.update(GH_TOKEN="inherited", GITHUB_TOKEN="inherited",
                        GH_ENTERPRISE_TOKEN="inherited", GITHUB_ENTERPRISE_TOKEN="inherited",
                        GH_HOST="wrong.example")

        def call(login):
            return self.run_command([
                ROOT / "shell/.local/bin/with-github", login, "gh",
                "api", "a path with spaces", "--jq", ".login"
            ])

        with concurrent.futures.ThreadPoolExecutor() as pool:
            results = list(pool.map(call, ["personal", "work"]))
        for login, result in zip(["personal", "work"], results):
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(),
                             [login, "api", "a path with spaces", "--jq", ".login"])
        self.assertEqual(self.env["GH_TOKEN"], "inherited")

    def test_github_missing_or_empty_token_never_runs_child(self):
        self.mock_gh()
        for login in ["missing", "empty"]:
            result = self.run_command([
                ROOT / "shell/.local/bin/with-github", login, "gh", "api", "user"
            ])
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_github_aliases_use_local_login_files(self):
        self.mock_gh()
        config = self.home / ".config/github"
        config.mkdir(parents=True)
        for role in ["personal", "work"]:
            (config / f"{role}-user").write_text(f"{role}-account\n")
            result = self.run_command([ROOT / f"shell/.local/bin/gh-{role}", "api", "user"])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines()[0], f"{role}-account")
        (config / "work-user").write_text("not a login\n")
        self.assertNotEqual(self.run_command([ROOT / "shell/.local/bin/gh-work", "api", "user"]).returncode, 0)

    def test_git_personal_identity_is_default_and_work_overrides_it(self):
        (self.home / ".gitconfig").symlink_to(ROOT / "git/.gitconfig")
        config = self.home / ".config/git"
        config.mkdir(parents=True)
        (config / "personal.gitconfig").write_text("[user]\n    email = personal@example.com\n")
        (config / "work.gitconfig").write_text("[user]\n    email = work@example.com\n")
        for name, expected in [("other", "personal@example.com"),
                               ("Developer/work/project", "work@example.com")]:
            repository = self.home / name
            repository.mkdir(parents=True)
            result = self.run_command(["git", "init", "--quiet", repository])
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.run_command(["git", "-C", repository, "config", "--get", "user.email"])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), expected)

    def test_composer_uses_php_from_path_and_preserves_arguments(self):
        data = self.home / ".local/share/composer"
        data.mkdir(parents=True)
        (data / "composer.phar").write_text("test only")
        self.fake("php", 'printf "%s\\n" "$@"')
        result = self.run_command([ROOT / "macos/.local/bin/composer", "run", "a b"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [str(data / "composer.phar"), "run", "a b"])

    def test_composer_missing_phar_fails(self):
        result = self.run_command([ROOT / "macos/.local/bin/composer", "--version"])
        self.assertNotEqual(result.returncode, 0)

    def test_composer_bad_download_preserves_existing_phar(self):
        data = self.home / ".local/share/composer"
        data.mkdir(parents=True)
        phar = data / "composer.phar"
        phar.write_text("previous installation")
        self.fake("curl", '''
while [[ $# -gt 0 ]]; do
  if [[ "$1" == --output ]]; then printf 'corrupt' > "$2"; exit 0; fi
  shift
done
exit 1
''')
        result = self.run_command(["bash", ROOT / "bootstrap/macos/install-composer.sh"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum mismatch", result.stderr)
        self.assertEqual(phar.read_text(), "previous installation")
        self.assertEqual(list(data.glob(".composer.*")), [])

    @unittest.skipUnless(shutil.which("direnv"), "direnv is needed for the integration test")
    def test_php_versions_coexist_with_real_direnv(self):
        config = self.home / ".config/direnv"
        config.mkdir(parents=True)
        shutil.copyfile(ROOT / "macos/.config/direnv/direnvrc", config / "direnvrc")
        self.fake("brew", '''
[[ $# == 2 && "$1" == --prefix ]] || exit 90
printf '%s/php installs/%s\\n' "$TEST_ROOT" "$2"
''')
        projects = []
        for version in ["7.4", "8.5"]:
            php = self.base / "php installs" / f"php@{version}" / "bin/php"
            php.parent.mkdir(parents=True)
            php.write_text(f"#!/bin/bash\nprintf '%s\\n' '{version}'\n")
            php.chmod(0o755)
            project = self.base / f"project-{version}"
            project.mkdir()
            (project / ".envrc").write_text(f"strict_env\nuse php php@{version}\n")
            result = self.run_command(["direnv", "allow", project])
            self.assertEqual(result.returncode, 0, result.stderr)
            projects.append(project)
        initial_path = self.env["PATH"]
        with concurrent.futures.ThreadPoolExecutor() as pool:
            results = list(pool.map(
                lambda p: self.run_command(["direnv", "exec", p, "php"]), projects
            ))
        for version, result in zip(["7.4", "8.5"], results):
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), version)
        self.assertEqual(self.env["PATH"], initial_path)
        # Missing binaries fail instead of falling back to a global PHP.
        (self.base / "php installs/php@7.4/bin/php").unlink()
        missing = self.run_command(["direnv", "exec", projects[0], "php"])
        self.assertNotEqual(missing.returncode, 0, missing.stdout + missing.stderr)

    def setup_tm(self, content):
        listing = self.base / "exclusions.txt"
        listing.write_text(content)
        self.fake("sudo", 'printf "%s\\n" "$*" >> "$TEST_ROOT/applied"')
        self.fake("tmutil", 'printf "%s\\n" "$*"')
        return listing

    def test_tm_check_does_not_apply_and_handles_spaces(self):
        (self.home / "cache with spaces").mkdir()
        listing = self.setup_tm("# comment\n~/cache with spaces\n")
        result = self.run_command(["bash", ROOT / "bootstrap/macos/timemachine.sh", "--check", listing])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(self.home / "cache with spaces"), result.stdout)
        self.assertFalse((self.base / "applied").exists())

    def test_tm_apply_fixed_path_even_before_creation(self):
        listing = self.setup_tm("~/future-cache\n")
        result = self.run_command(["bash", ROOT / "bootstrap/macos/timemachine.sh", "--apply", listing])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.base / "applied").read_text().strip(),
                         f"tmutil addexclusion -p {self.home}/future-cache")

    def test_tm_invalid_list_is_rejected_before_any_change(self):
        for bad in ["/", str(self.home), "~/../other", "~/cache/*", "relative-path", "~/cache/$VAR"]:
            listing = self.setup_tm(f"~/valid-cache\n{bad}\n")
            result = self.run_command(["bash", ROOT / "bootstrap/macos/timemachine.sh", "--apply", listing])
            self.assertNotEqual(result.returncode, 0, bad)
            self.assertFalse((self.base / "applied").exists(), bad)

    def test_tm_empty_list_is_valid(self):
        listing = self.setup_tm("# nothing yet\n")
        result = self.run_command(["bash", ROOT / "bootstrap/macos/timemachine.sh", "--check", listing])
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("docker"), "Docker Compose CLI is needed")
    def test_compose_configuration_and_required_optional_versions(self):
        # Prefer the standalone CLI: a temporary HOME has no user plugin config.
        compose = [shutil.which("docker-compose")] if shutil.which("docker-compose") else ["docker", "compose"]
        for key in ["MYSQL_ROOT_PASSWORD", "MYSQL_PASSWORD", "POSTGRES_PASSWORD",
                    "REDIS_IMAGE", "MEILISEARCH_IMAGE", "MEILI_MASTER_KEY", "COMPOSE_PROFILES"]:
            self.env.pop(key, None)
        command = compose + ["--env-file", "/dev/null", "-f", ROOT / "services/compose.yaml",
                   "--profile", "*", "config", "--format", "json"]
        result = self.run_command(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        services = json.loads(result.stdout)["services"]
        self.assertEqual(set(services), {"mailpit"})
        for service in services.values():
            self.assertIn("@sha256:", service["image"])
            self.assertEqual(service["platform"], "linux/arm64")
            self.assertEqual(service["restart"], "no")
            for port in service["ports"]:
                self.assertEqual(port["host_ip"], "127.0.0.1")
        for filename in ["compose.redis.yaml", "compose.meilisearch.yaml"]:
            result = self.run_command(compose + ["--env-file", "/dev/null", "-f",
                                       ROOT / "services" / filename, "config", "--quiet"])
            self.assertNotEqual(result.returncode, 0)
        self.env.update(REDIS_IMAGE="redis:test-only", MEILISEARCH_IMAGE="getmeili/meilisearch:test-only",
                        MEILI_MASTER_KEY="test-only-not-a-secret")
        for filename in ["compose.redis.yaml", "compose.meilisearch.yaml"]:
            result = self.run_command(compose + ["--env-file", "/dev/null", "-f",
                                       ROOT / "services" / filename, "config", "--quiet"])
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("stow"), "Stow is needed for the deployment test")
    def test_stow_deploys_into_temporary_home_and_detects_conflict(self):
        command = ["stow", "--dir", ROOT, "--target", self.home,
                   "shell", "git", "vim", "btop", "macos"]
        result = self.run_command(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / ".config/direnv/direnvrc").resolve(),
                         ROOT / "macos/.config/direnv/direnvrc")
        for name in ["composer", "with-github", "gh-personal", "gh-work"]:
            self.assertTrue(os.access(self.home / ".local/bin" / name, os.X_OK), name)
        other = self.base / "existing-home"
        (other / ".config/direnv").mkdir(parents=True)
        existing = other / ".config/direnv/direnvrc"
        existing.write_text("existing helper\n")
        result = self.run_command(["stow", "--simulate", "--dir", ROOT,
                                   "--target", other, "macos"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(existing.read_text(), "existing helper\n")


if __name__ == "__main__":
    unittest.main()
