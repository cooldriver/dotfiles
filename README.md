# Dotfiles

Personal macOS and Linux configuration managed with GNU Stow. This is a public
repository: never add secrets, private keys, tokens, passwords, or confidential
data.

## Stow Packages

| Package | Target | Contents |
| --- | --- | --- |
| `shell` | macOS and Linux | Zsh, aliases, optional integrations, and per-account GitHub CLI launchers |
| `git` | macOS and Linux | Shared Git settings |
| `vim` | macOS and Linux | Minimal Vim configuration |
| `btop` | macOS and Linux | Portable btop preferences |
| `zellij` | macOS and Linux | Shared terminal multiplexer settings |
| `macos` | macOS | OrbStack integration, project-local PHP selection, and Composer launcher |

`brew`, `bootstrap`, `docs`, `services`, and `tests` are not deployed with Stow.
See the [manual macOS guide](docs/macos-installation.md) for PHP 7.4/8.5,
Composer/Xdebug, 1Password, GitHub accounts, and Time Machine exclusions.
Local databases and mail capture are described in [services](services/README.md).
Shell history and private per-host sync are described in [Atuin](docs/atuin.md).
See [Zellij](docs/zellij.md) for installation and session handling on both systems.

## macOS Bootstrap

1. Install Homebrew from its official website.
2. Clone this repository, review the Brewfile, then follow the staged Homebrew
   installation in the [macOS guide](docs/macos-installation.md). To install the
   complete reviewed list at once (after App Store sign-in):

   ```bash
   git clone https://github.com/<account>/dotfiles.git ~/Developer/personal/dotfiles
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
   `<email> <public SSH key>`. These files remain outside this repository.

5. Add the GitHub host aliases from `docs/ssh-github-config.example` to your
   local SSH configuration. Use `github-personal` or `github-work` in remotes.

6. Preview deployment and resolve existing-file conflicts before applying:

   ```bash
   stow --simulate --verbose --target "$HOME" shell git vim btop zellij macos
   stow --target "$HOME" shell git vim btop zellij macos
   chsh -s "$(command -v zsh)"
   ```

7. Open a new login shell, install the Composer PHAR with
   `bash bootstrap/macos/install-composer.sh`, then configure the remaining local
   settings and run the checks from the macOS guide. No services or backup
   exclusions are applied automatically by Stow.

## Linux Bootstrap

The Debian-based bootstrap installs the terminal tools required by the dotfiles
and their optional integrations. The `server` profile also installs the
administration tools used by the homelab runbook.

```bash
git clone https://github.com/<account>/dotfiles.git ~/src/dotfiles
cd ~/src/dotfiles
bootstrap/linux/server.sh
stow --simulate --verbose --target "$HOME" shell git vim btop zellij
stow --target "$HOME" shell git vim btop zellij
```

Before creating commits, configure the personal identity used by every Linux
repository:

```bash
mkdir -p ~/.config/git
cp docs/git-identities.example.gitconfig ~/.config/git/personal.gitconfig
```

Set the personal name, email, and public signing key in that local file. Create
`~/.ssh/allowed_signers` with one `<email> <public SSH key>` entry for each
identity. It is also the default identity on macOS; `~/Developer/work/`
overrides it with the work identity.

Use `bootstrap/linux/common.sh` when only the shared shell environment is
needed. A desktop profile can be added later without changing the server
profile. Optional packages unavailable in a distribution release are skipped,
and their shell integrations remain inactive.

## Updating

```bash
git pull --ff-only
stow --restow --target "$HOME" shell git vim btop zellij
```

For changes to an existing deployed file, `git pull --ff-only` is enough: the
symbolic link already points into the repository. Run `stow --restow` when a
commit adds, removes, moves, or changes the deployment path of files. It is
also safe to run after every pull. On macOS, add `macos` to the command. Update
cloned dependencies separately in `~/.oh-my-zsh`.

## Persisting Changes

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

## Local Files

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
- `~/.config/dev-services/local.env` holds local Compose parameters and passwords.
- `~/.config/timemachine/exclusions.txt` holds the reviewed exclusion paths.
- Prefer AWS profiles, `gh auth login`, secret managers, and `direnv` over
  exporting credentials in the shell.
