# Dotfiles

My macOS and Debian-based Linux setup, built around Zsh and deployed with
[GNU Stow](https://www.gnu.org/software/stow/). The same small set of terminal
configurations follows me between Macs and homelab servers; macOS-only settings
stay in a separate package. Dependencies and machine-specific setup are kept
explicit rather than hidden behind a one-command installer.

This is a personal, public repository, not a ready-made configuration for every
machine. Review the packages and scripts before using them. Never add secrets,
private keys, tokens, passwords, or confidential data.

Currently designed for and tested on **macOS 27**, **Debian 13**, and
**Ubuntu 26.04**. Other versions or Debian-based distributions may work, but
are not part of the tested setup.

## Start here

- **Setting up a Mac?** Follow [macOS bootstrap](#macos-bootstrap), then the
  [manual macOS guide](docs/macos-installation.md).
- **Setting up a Debian-based server?** Follow [Linux bootstrap](#linux-bootstrap).
- **Already installed?** See [updating](#updating) and
  [persisting changes](#persisting-changes), or
  [removing Stow links](#removing-stow-links).
- **Adapting this setup?** Review the [Stow packages](#stow-packages) and
  [local files](#local-files) before deploying anything.

## Stow packages

| Package | Target | Contents |
| --- | --- | --- |
| `shell` | macOS and Linux | Zsh, Spaceship prompt, aliases, optional integrations, and per-account GitHub CLI launchers |
| `linux-server` | Linux servers, explicit opt-in with `shell` | Automatic private Atuin sync for permanent Gamorr access |
| `git` | macOS and Linux | Shared Git settings |
| `vim` | macOS and Linux | Minimal Vim configuration |
| `zellij` | macOS and Linux | Shared terminal multiplexer settings |
| `lazygit` | macOS and Linux | Syntax-highlighted diffs using delta |
| `macos` | macOS | OrbStack integration, project-local PHP selection, and Composer launcher |
| `ssh` | macOS workstations, explicit opt-in | Public SSH scaffold; restore personal rules first, deploy with `--no-folding` |

`brew`, `bootstrap`, `docs`, `services`, `scripts`, `tests`, and `private` are not deployed with Stow.
Stow links the selected package files into `$HOME`; it does not install software
or apply the optional services. Preview links and resolve existing-file conflicts
before deploying.
See [AGENTS.md](AGENTS.md) for repository guidance when working with coding agents.

### Related guides

- [Encrypted personal SSH configuration](docs/ssh.md): optional macOS workflow, local public keys and 1Password agent, age-encrypted backup and explicit restore. Not initialized or deployed automatically.

- [Manual macOS setup](docs/macos-installation.md): PHP 7.4/8.5,
  Composer/Xdebug, 1Password, GitHub accounts, and Time Machine exclusions.
- [Local development services](services/README.md): DBngin databases and
  OrbStack services.
- [Atuin](docs/atuin.md): shell history and private per-host sync. Toola's
  optional LAN-only LaunchAgent requires a separate installation; Stow does not
  activate it.
- [Zellij](docs/zellij.md): installation and session handling on both systems.

The `shell` package also deploys `~/.spaceshiprc.zsh`: it moves the time to the
right and the directory after the host, hides the Docker/OrbStack section,
always shows user and host, and reports failed commands. Other Spaceship
sections keep their default order. Spaceship loads this file automatically
when installed. Shell aliases live in
[`shell/.config/zsh/aliases.zsh`](shell/.config/zsh/aliases.zsh).

### eza shortcuts

When `eza` is installed, these shortcuts always enable colors and icons, without enabling hyperlinks. They do not replace `ls`.

| Alias | View | Example |
| --- | --- | --- |
| `lz` | Quick grid, sorted by name | `lz` |
| `lzl` | Long listing with a header, octal permissions, directories first and a size color scale | `lzl -a` |
| `lzr` | Long listing with a header, newest modifications first, relative dates and an age color scale | `lzr ~/Downloads` |
| `lzg` | Long listing with a header, hidden files and Git status, directories first | `lzg` |
| `lzt` | Tree limited to two levels, without metadata | `lzt --level=3` |

Extra options and paths are passed to eza normally: `lz -a` includes hidden files, `lzt --git-ignore` hides Git-ignored entries, and `lzt --long --header` adds metadata. Only `lzl` and `lzg` group directories first; `lzr` sorts files and directories together by modification time. Git-ignored entries remain visible by default, including in `lzg`.

`lzr` replaces the old `lat` shortcut and lists all entries rather than truncating to ten. `lz` is now a lightweight grid; use `lzg` for Git details. Recursive directory sizes are deliberately left to dedicated disk-usage tools. Colors and icons remain enabled even when piping these shortcuts; use plain `eza` or `ls` when that is undesirable. Open a new shell after updating to discard old alias definitions.

### Shell navigation and diagnostics

`hpath` lists PATH entries alphabetically for scanning; `hpath --ordered` preserves their actual command-search order. Both views prefix each entry with its original position in PATH (starting at 1), so the same number always indicates the same search priority regardless of display order. Each entry is printed on its own line, without removing duplicates.

With the configured Oh My Zsh Git plugin, `grt` (Git RooT) returns to the current repository's root. Use `cd -` to return to the previous directory.

## macOS bootstrap

1. Install Homebrew from its official website.
2. Clone this repository, review the Brewfile, then follow the staged Homebrew
   installation in the [macOS guide](docs/macos-installation.md). To install the
   complete reviewed list at once (after App Store sign-in):

   ```bash
   git clone https://github.com/cooldriver/dotfiles.git ~/Developer/personal/dotfiles
   cd ~/Developer/personal/dotfiles
   brew bundle --file brew/Brewfile
   ```

3. Install shell dependencies from explicit Git clones:

   ```bash
   git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git ~/.oh-my-zsh
   git clone --depth=1 https://github.com/spaceship-prompt/spaceship-prompt.git \
     ~/.oh-my-zsh/custom/themes/spaceship-prompt
   ln -sfn ~/.oh-my-zsh/custom/themes/spaceship-prompt/spaceship.zsh-theme \
     ~/.oh-my-zsh/custom/themes/spaceship.zsh-theme
   ```

4. Create local Git identity files before working in the matching directories:

   ```bash
   mkdir -p ~/.config/git
   cp docs/git-identities.example.gitconfig ~/.config/git/personal.gitconfig
   cp docs/git-identities.example.gitconfig ~/.config/git/work.gitconfig
   ```

   Set the appropriate identity and public signing key in each file. Create
   `~/.ssh/allowed_signers` with one line per profile in the form
   `<email> <public SSH key>`. The shared Git configuration uses this file to
   verify SSH signatures; the 1Password signing program is macOS-only. These
   files remain outside this repository.

5. Follow the [encrypted SSH workflow](docs/ssh.md) to restore personal rules and explicitly deploy the public SSH scaffold. It defines the existing `personalgit` and `workgit` aliases; the restored private rules select their local public-key paths. Export the matching public keys from 1Password to those paths. Use these aliases in remotes. The standard Stow command below does not deploy the optional `ssh` package.

6. Preview deployment and resolve existing-file conflicts before applying:

   ```bash
    stow --simulate --verbose --target "$HOME" shell git vim zellij lazygit macos
    stow --target "$HOME" shell git vim zellij lazygit macos
   chsh -s "$(command -v zsh)"
   ```

7. Open a new login shell, install the Composer PHAR with
   `bash bootstrap/macos/install-composer.sh`, then configure the remaining local
   settings and run the checks from the macOS guide. No services or backup
   exclusions are applied automatically by Stow.

## Linux bootstrap

The Debian-based bootstrap installs the terminal tools required by the dotfiles
and their optional integrations. The `server` profile also installs the
administration tools used by the homelab runbook.

The server profile installs Atuin through its official standalone release installer into `~/.atuin/bin`, with a receipt supporting `atuin update`; it does not install the older APT client. The initial verified release is 18.24.1, not a version hold: an existing supported standalone installation is preserved, never downgraded, and future updates use `atuin update --check` then `atuin update`. These updates are not managed by APT or scheduled automatically. Interactive Linux Zsh prefers this client before initialization; macOS keeps its package-manager selection. The explicit `linux-server` Stow package enables private sync every five minutes of shell activity, as on Tatooine; deploy it only on servers with permanent access to Gamorr, together with `shell`. Follow the [Atuin guide](docs/atuin.md) for installation, migration precautions and interactive login. The common profile already includes optional `zsh-syntax-highlighting`, loaded last by Zsh when installed.

```bash
git clone https://github.com/cooldriver/dotfiles.git ~/src/dotfiles
cd ~/src/dotfiles
bootstrap/linux/server.sh
stow --simulate --verbose --target "$HOME" shell linux-server git vim zellij lazygit
stow --target "$HOME" shell linux-server git vim zellij lazygit
```

Start `zsh` to try the deployed shell configuration. If you want it as your
login shell, change it explicitly after checking that it works:

```bash
chsh -s "$(command -v zsh)"
```

Log out and back in for the login-shell change to take effect. The bootstrap
does not change your login shell automatically.

Before creating commits, configure the personal identity used by every Linux
repository:

```bash
mkdir -p ~/.config/git
cp docs/git-identities.example.gitconfig ~/.config/git/personal.gitconfig
```

Set the personal name, email, and public signing key in that local file. Create
`~/.ssh/allowed_signers` with one `<email> <public SSH key>` entry for each
identity. It is also the default identity on macOS; `~/Developer/work/`
overrides it with the work identity. The shared Git configuration uses
`~/.ssh/allowed_signers` to verify SSH signatures on both systems.

Use `bootstrap/linux/common.sh` when only the shared shell environment is
needed. A desktop profile can be added later without changing the server
profile. Optional packages unavailable in a distribution release are skipped,
and their shell integrations remain inactive. Lazygit is one such optional APT
package: it is available in Debian 13 and Ubuntu 26.04, but not Ubuntu 24.04.
If unavailable, its Stow configuration can still be deployed; install Lazygit
separately from a source you trust if you want to use it. The `git-delta` APT
package is required by the shared Git configuration and provides Lazygit's
`delta` diff previews when Lazygit is installed.

## Development checks

Use [AGENTS.md](AGENTS.md) for safety rules and the independent review process. Install the pinned Python linter in an isolated environment with `python -m pip install -r requirements-dev.txt`. Static shell checks require Bash, Zsh, and ShellCheck; optional integration tests use Stow, direnv, Docker Compose, and age when available. CI installs age to exercise real encryption/restoration with synthetic identities; no personal credentials are used.

```sh
bash scripts/check-shell.sh
python -m ruff check --no-cache .
python -B scripts/check-tests.py
git diff --check
```

The GitHub workflow runs on Ubuntu and macOS with minimal permissions and commit-pinned actions. Tests use temporary homes and fake commands, not real bootstrap, services, or credentials. The identity test initializes a temporary Git repository; agents exclude it locally under the repository's Git rule and report the exclusion, while CI runs it. Optional skipped tests must be reported; CI is not proof of deployment on the personal machines or Debian servers.

## Updating

If updating an old checkout that still deploys btop, complete the btop unlinking step below **before** running `git pull`: the removal commit cannot detach existing Stow links automatically.

```bash
git pull --ff-only
stow --restow --target "$HOME" shell git vim zellij lazygit
```

For changes to an existing deployed file, `git pull --ff-only` is enough: the
symbolic link already points into the repository. Run `stow --restow` when a
commit adds, removes, moves, or changes the deployment path of files. It is
also safe to run after every pull. On macOS, add `macos` to the command. Update
cloned dependencies separately in `~/.oh-my-zsh`.

The `lazygit` package stores its shared configuration in
`~/.config/lazygit/config.yml`. Interactive Zsh sets `LG_CONFIG_FILE` so Lazygit
uses it on macOS as well as Linux. Diff previews use the installed `delta`
binary and inherit its appearance settings from `git/.gitconfig`.

### btop: installed, with local configuration only

btop remains installed by `brew/Brewfile` on macOS and the common Linux bootstrap. Its configuration and runtime logs are no longer shared or managed by Stow. Let the installed version generate its own local defaults; no reference file, copy helper, or Git flags are needed. Versions 1.3.2 and 1.4.7 rewrite the configuration differently, so a generated file is not a portable shared reference.

**Existing deployments: unlink before pulling the removal commit.** Close btop first. From the old checkout, while the `btop` package still exists, preview only its removal:

```sh
stow --simulate --verbose --delete --target "$HOME" btop
```

Check that only btop links belonging to this checkout are removed, then run:

```sh
stow --verbose --delete --target "$HOME" btop
```

This does not uninstall btop or remove ordinary local files. The old shared preferences will no longer be used; preserve a copy outside the checkout first only if wanted. After unlinking, verify that neither the btop configuration directory nor its configuration file resolves into this repository before launching btop again. Existing independent local configuration should be left untouched. If a parent configuration directory is still linked into the checkout, or Stow reports a conflict, stop and inspect rather than forcing links. Once detached, pull the removal commit; the next normal launch can generate local configuration. Discard only unwanted tracked btop configuration changes if they block the pull; never restore the whole repository or clean other files. Old logs may remain in the retired package directory: inspect and remove only known btop runtime files if desired, never use a global clean. If the commit was already pulled, inspect dangling links and their targets before any manual repair; the old package is no longer available for Stow deletion.

## Removing Stow links

From the repository root, preview removal for the packages you want to stop
using, then remove only those links:

```bash
stow --simulate --verbose --delete --target "$HOME" shell git vim zellij lazygit
stow --delete --target "$HOME" shell git vim zellij lazygit
```

On macOS, add `macos` to both commands if you also want to remove that package.
This unlinks Stow-managed files; it does not uninstall software, delete local
identity or secret files, or undo separate setup steps described in the guides.
Review the preview before running the second command.

## Persisting changes

Edit configuration files from the repository working tree whenever possible.
Files deployed by Stow are symbolic links, so editing a deployed file also
changes its source in the repository.

Review and publish an intentional change with:

```bash
cd ~/Developer/personal/dotfiles
git status
git diff
git diff --check
git add <changed-files>
git commit -m "Describe the change"
git push
```

Before committing, verify that no secret or machine-specific value has been
added. On another machine, pull the commit and run the update command above to
refresh Stow links when the change affects the deployed file structure.

## Local files

- Interactive Zsh defaults `EDITOR` and `VISUAL` to `vim` on both macOS and
  Linux. Override them in a local or host Zsh file if needed.
- `~/.config/zsh/local.zsh` is reserved for local settings and secrets that
  cannot be managed by a dedicated tool.
- `~/.config/zsh/hosts/<hostname>.zsh` contains non-sensitive, versioned shell
  settings for a specific host. It is deployed with the `shell` package, but
  Zsh loads only the file matching `hostname -s`, converted to lowercase.
- `~/.config/git/personal.gitconfig` and `~/.config/git/work.gitconfig` hold
  Git identities and signing keys.
- `~/.ssh/config` and private SSH keys remain outside this repository.
- `~/.config/github/personal-user` and `work-user` hold GitHub logins only;
  tokens are retrieved from `gh` at invocation time.
- `~/.config/dev-services/local.env` holds local Compose parameters for Mailpit,
  Redis and Meilisearch; SQL instance credentials remain in DBngin or local
  credential storage, outside this repository.
- `~/.config/timemachine/exclusions.txt` holds the reviewed exclusion paths.
- Prefer AWS profiles, `gh auth login`, secret managers, and `direnv` over
  exporting credentials in the shell.

## License

[MIT](LICENSE) © 2026 Hervé Weltzer.
