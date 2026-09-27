#!/bin/bash
set -euo pipefail

if [[ "$(uname -s)" != Darwin || "$(hostname -s | tr '[:upper:]' '[:lower:]')" != toola ]]; then
  printf '%s\n' 'This LaunchAgent may only be installed on Toola (macOS).' >&2
  exit 1
fi

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
source_script="$repo_root/services/macos/toola-atuin-sync.sh"
source_plist="$repo_root/services/macos/com.fieldbook.toola-atuin-sync.plist"
target_script="$HOME/.local/bin/toola-atuin-sync"
target_plist="$HOME/Library/LaunchAgents/com.fieldbook.toola-atuin-sync.plist"
label="com.fieldbook.toola-atuin-sync"
domain="gui/$(id -u)"

# Do not overwrite a pre-existing installation or unrelated user files.
for pair in "$source_script:$target_script" "$source_plist:$target_plist"; do
  source_file="${pair%%:*}"
  target_file="${pair#*:}"
  if [[ -e "$target_file" || -L "$target_file" ]]; then
    if [[ -L "$target_file" ]] || ! cmp -s "$source_file" "$target_file"; then
      printf 'Existing file differs; inspect it before installing: %s\n' "$target_file" >&2
      exit 1
    fi
  fi
done

plutil -lint "$source_plist" >/dev/null
mkdir -p "$HOME/.local/bin" "$HOME/Library/LaunchAgents"
install -m 0755 "$source_script" "$target_script"
install -m 0644 "$source_plist" "$target_plist"

if launchctl print "$domain/$label" >/dev/null 2>&1; then
  printf 'Already loaded: %s. No reload was performed.\n' "$label"
else
  launchctl bootstrap "$domain" "$target_plist"
  printf 'Loaded %s on Toola.\n' "$label"
fi
