# Dotfiles

Personal macOS and Linux configuration managed with GNU Stow. This is a public
repository: never add secrets, private keys, tokens, passwords, or confidential
data.

## Stow Packages

| Package | Target | Contents |
| --- | --- | --- |
| `shell` | macOS and Linux | Zsh, aliases, and optional integrations |
| `git` | macOS and Linux | Shared Git settings |
| `vim` | macOS and Linux | Minimal Vim configuration |
| `btop` | macOS and Linux | Portable btop preferences |
| `macos` | macOS | Conditional OrbStack integration |

`brew` is not deployed with Stow. It contains the macOS Brewfile.

## macOS Bootstrap

1. Install Homebrew from its official website.
2. Clone this repository, then install applications and command-line tools:

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
   mkdir -p ~/.local/share
   git clone --depth=1 https://github.com/junegunn/fzf-git.sh.git \
     ~/.local/share/fzf-git
   ```

4. Create local Git identity files before working in the matching directories:

   ```bash
   mkdir -p ~/.config/git
   cp docs/git-identities.example.gitconfig ~/.config/git/personal.gitconfig
   cp docs/git-identities.example.gitconfig ~/.config/git/work.gitconfig
   ```

   Set the appropriate identity and public signing key in each file. These files
   remain outside this repository.

5. Add the GitHub host aliases from `docs/ssh-github-config.example` to your
   local SSH configuration. Use `github-personal` or `github-work` in remotes.

6. Deploy the packages:

   ```bash
   stow --target "$HOME" shell git vim btop macos
   chsh -s "$(command -v zsh)"
   ```

## Linux Bootstrap

The Debian-based bootstrap installs the terminal tools required by the dotfiles
and their optional integrations. The `server` profile also installs the
administration tools used by the homelab runbook.

```bash
git clone https://github.com/<account>/dotfiles.git ~/src/dotfiles
cd ~/src/dotfiles
bootstrap/linux/server.sh
stow --target "$HOME" shell git vim btop
```

Use `bootstrap/linux/common.sh` when only the shared shell environment is
needed. A desktop profile can be added later without changing the server
profile. Optional packages unavailable in a distribution release are skipped,
and their shell integrations remain inactive.

## Updating

```bash
git pull --ff-only
stow --restow --target "$HOME" shell git vim btop
```

For changes to an existing deployed file, `git pull --ff-only` is enough: the
symbolic link already points into the repository. Run `stow --restow` when a
commit adds, removes, moves, or changes the deployment path of files. It is
also safe to run after every pull. On macOS, add `macos` to the command. Update
cloned dependencies separately in `~/.oh-my-zsh` and `~/.local/share/fzf-git`.

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
  Zsh loads only the file matching `hostname -s`.
- `~/.config/git/personal.gitconfig` and `~/.config/git/work.gitconfig` hold
  Git identities and signing keys.
- `~/.ssh/config` and private SSH keys remain outside this repository.
- Prefer AWS profiles, `gh auth login`, secret managers, and `direnv` over
  exporting credentials in the shell.
