#!/usr/bin/env bash

set -euo pipefail

require_apt() {
  if ! command -v apt-get >/dev/null 2>&1; then
    printf '%s\n' 'This bootstrap supports Debian-based distributions only.' >&2
    exit 1
  fi
}

run_privileged() {
  if [[ $(id -u) -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

prepare_apt() {
  require_apt
  run_privileged apt-get update
}

install_required() {
  run_privileged apt-get install --yes "$@"
}

install_optional() {
  local package
  local packages=()

  for package in "$@"; do
    if apt-cache show "$package" >/dev/null 2>&1; then
      packages+=("$package")
    else
      printf 'Skipping unavailable optional package: %s\n' "$package" >&2
    fi
  done

  if ((${#packages[@]})); then
    run_privileged apt-get install --yes "${packages[@]}"
  fi
}

install_common_packages() {
  install_required zsh git vim btop fzf tmux stow
  install_optional bat direnv fd-find git-delta eza fastfetch jq ripgrep shellcheck zoxide
}

clone_if_missing() {
  local repository=$1
  local destination=$2

  if [[ -e "$destination" || -L "$destination" ]]; then
    printf 'Keeping existing dependency: %s\n' "$destination"
    return
  fi

  mkdir -p "$(dirname "$destination")"
  git clone --depth=1 "$repository" "$destination"
}

install_shell_dependencies() {
  local spaceship_dir="$HOME/.oh-my-zsh/custom/themes/spaceship-prompt"
  local spaceship_theme="$HOME/.oh-my-zsh/custom/themes/spaceship.zsh-theme"

  clone_if_missing https://github.com/ohmyzsh/ohmyzsh.git "$HOME/.oh-my-zsh"
  clone_if_missing https://github.com/spaceship-prompt/spaceship-prompt.git "$spaceship_dir"

  if [[ ! -e "$spaceship_theme" && ! -L "$spaceship_theme" ]]; then
    ln -s "spaceship-prompt/spaceship.zsh-theme" "$spaceship_theme"
  fi

  clone_if_missing https://github.com/junegunn/fzf-git.sh.git "$HOME/.local/share/fzf-git"
}

main() {
  prepare_apt
  install_common_packages
  install_shell_dependencies
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  main "$@"
fi
