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
| `git` | macOS and Linux | Shared Git settings |
| `vim` | macOS and Linux | Minimal Vim configuration |
| `btop` | macOS and Linux | Portable btop preferences |
| `zellij` | macOS and Linux | Shared terminal multiplexer settings |
| `lazygit` | macOS and Linux | Syntax-highlighted diffs using delta |
| `macos` | macOS | OrbStack integration, project-local PHP selection, and Composer launcher |

`brew`, `bootstrap`, `docs`, `services`, and `tests` are not deployed with Stow.
Stow links the selected package files into `$HOME`; it does not install software
or apply the optional services. Preview links and resolve existing-file conflicts
before deploying.
See [AGENTS.md](AGENTS.md) for repository guidance when working with coding agents.

### Related guides

- [Manual macOS setup](docs/macos-installation.md): PHP 7.4/8.5,
  Composer/Xdebug, 1Password, GitHub accounts, and Time Machine exclusions.
- [Local development services](services/README.md): DBngin databases and
  OrbStack services.
- [Atuin](docs/atuin.md): shell history and private per-host sync. Toola's
  optional LAN-only LaunchAgent requires a separate installation; Stow does not
  activate it.
- [Zellij](docs/zellij.md): installation and session handling on both systems.

The `shell` package also deploys `~/.spaceshiprc.zsh`: it moves the time to the
right and the directory after the host, always shows user and host, and reports
failed commands. Other Spaceship sections keep their default order. Spaceship
loads this file automatically when installed. Shell aliases live in
[`shell/.config/zsh/aliases.zsh`](shell/.config/zsh/aliases.zsh).

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

5. Add the GitHub host aliases from `docs/ssh-github-config.example` to your
   local SSH configuration. Use `github-personal` or `github-work` in remotes.

6. Preview deployment and resolve existing-file conflicts before applying:

   ```bash
    stow --simulate --verbose --target "$HOME" shell git vim btop zellij lazygit macos
    stow --target "$HOME" shell git vim btop zellij lazygit macos
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

```bash
git clone https://github.com/cooldriver/dotfiles.git ~/src/dotfiles
cd ~/src/dotfiles
bootstrap/linux/server.sh
stow --simulate --verbose --target "$HOME" shell git vim btop zellij lazygit
stow --target "$HOME" shell git vim btop zellij lazygit
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

## Updating

```bash
git pull --ff-only
stow --restow --target "$HOME" shell git vim btop zellij lazygit
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

## Removing Stow links

From the repository root, preview removal for the packages you want to stop
using, then remove only those links:

```bash
stow --simulate --verbose --delete --target "$HOME" shell git vim btop zellij lazygit
stow --delete --target "$HOME" shell git vim btop zellij lazygit
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
