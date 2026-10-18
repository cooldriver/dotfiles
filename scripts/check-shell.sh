#!/usr/bin/env bash
# Offline static checks only: never source configs or run installers.
set -euo pipefail
cd "$(dirname "$0")/.."

for tool in bash zsh shellcheck; do
  command -v "$tool" >/dev/null || {
    printf 'Required validation tool not found: %s\n' "$tool" >&2
    exit 1
  }
done

check_dir="$(mktemp -d)"
cleanup() {
  rm -f "$check_dir/bash" "$check_dir/zsh"
  rmdir "$check_dir"
}
trap cleanup EXIT

# Keep find outside process substitutions so discovery failures stop validation.
find bootstrap services scripts -type f -name '*.sh' -print0 > "$check_dir/bash"
find shell macos linux-server -type f \( -name '*.zsh' -o -name '*.zshrc' -o -name '.zshrc' -o -name '.zprofile' -o -name '.zshenv' -o -name '.zlogin' -o -name '.zlogout' \) -print0 > "$check_dir/zsh"

while IFS= read -r -d '' script; do
  printf 'Bash + ShellCheck: %s\n' "$script"
  bash -n "$script"
  shellcheck "$script"
done < "$check_dir/bash"

for script in shell/.local/bin/* macos/.local/bin/* macos/.config/direnv/direnvrc; do
  printf 'Bash + ShellCheck: %s\n' "$script"
  bash -n "$script"
  shellcheck "$script"
done

while IFS= read -r -d '' script; do
  printf 'Zsh syntax: %s\n' "$script"
  zsh -f -n "$script"
done < "$check_dir/zsh"
