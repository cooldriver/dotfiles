#!/usr/bin/env bash

set -euo pipefail

# Initial verified release, not a hold: future upgrades use `atuin update`.
version=18.24.1
checksum=69c7c0e057084ede4536de25f856c037f4649dcf8f29cc98a64ac52340320a99
binary="$HOME/.atuin/bin/atuin"
receipt="${XDG_CONFIG_HOME:-$HOME/.config}/atuin/atuin-receipt.json"

if [[ $(uname -s) != Linux ]]; then
  printf '%s\n' 'This installer is for Linux only.' >&2
  exit 1
fi
case "$(uname -m)" in
  x86_64|aarch64|arm64) ;;
  *) printf '%s\n' 'Unsupported Atuin architecture.' >&2; exit 1 ;;
esac

command -v python3 >/dev/null || { printf '%s\n' 'Python 3 is required to validate the Atuin update receipt.' >&2; exit 1; }

validate_receipt() {
  python3 - "$receipt" "$HOME/.atuin/bin" <<'PY'
import json
from pathlib import Path
import re
import sys

try:
    data = json.loads(Path(sys.argv[1]).read_text())
    source = data.get("source", {})
    valid = (
        all(source.get(key) == value for key, value in {
            "app_name": "atuin", "name": "atuin", "owner": "atuinsh",
            "release_type": "github",
        }.items())
        and Path(data["install_prefix"]).resolve() == Path(sys.argv[2]).resolve()
        and data.get("install_layout") == "flat"
        and isinstance(data.get("binaries"), list) and "atuin" in data["binaries"]
        and isinstance(data.get("modify_path"), bool)
        and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.+-]+)?", data["version"])
        and data.get("provider", {}).get("source") == "cargo-dist"
    )
    if not valid:
        raise ValueError("invalid receipt")
except (OSError, ValueError, TypeError, KeyError, AttributeError):
    print("Invalid or mismatched Atuin update receipt; inspect it before proceeding.", file=sys.stderr)
    sys.exit(1)
PY
}

if [[ -L "$HOME/.atuin" || -L "$HOME/.atuin/bin" ]]; then
  printf '%s\n' 'Refusing a symlinked standalone Atuin installation.' >&2
  exit 1
fi

if [[ -f "$binary" && -x "$binary" && ! -L "$binary" && -f "$receipt" && ! -L "$receipt" ]]; then
  validate_receipt
  current=$("$binary" --version)
  if [[ ! "$current" =~ ^atuin[[:space:]]+([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    printf '%s\n' 'Cannot identify the existing standalone Atuin version.' >&2
    exit 1
  fi
  major=${BASH_REMATCH[1]}
  minor=${BASH_REMATCH[2]}
  patch=${BASH_REMATCH[3]}
  if (( major < 18 || (major == 18 && minor < 24) || (major == 18 && minor == 24 && patch < 1) )); then
    printf 'Existing standalone client is too old: %s. Run %s update, then retry.\n' "$current" "$binary" >&2
    exit 1
  fi
  printf 'Keeping %s. Check future upgrades with: %s update --check\n' "$current" "$binary"
  exit 0
fi

if [[ -e "$HOME/.atuin" || -e "$receipt" || -L "$receipt" ]]; then
  printf '%s\n' 'Refusing to replace an unmanaged or partial Atuin installation; inspect it first.' >&2
  exit 1
fi

for tool in curl sha256sum; do
  command -v "$tool" >/dev/null || { printf 'Required tool not found: %s\n' "$tool" >&2; exit 1; }
done

umask 077
tmp=$(mktemp -d)
trap 'rm -f -- "$tmp/atuin-installer.sh"; rmdir -- "$tmp"' EXIT
curl --fail --show-error --location --proto '=https' --proto-redir '=https' --tlsv1.2 \
  --output "$tmp/atuin-installer.sh" \
  "https://github.com/atuinsh/atuin/releases/download/v$version/atuin-installer.sh"
printf '%s  %s\n' "$checksum" "$tmp/atuin-installer.sh" | sha256sum --check --status

# The release installer writes the update receipt but never edits shell startup files.
# Do not use setup.atuin.sh: that wrapper also sets up shells and agent hooks.
ATUIN_INSTALL_DIR="$HOME/.atuin/bin" ATUIN_NO_MODIFY_PATH=1 sh "$tmp/atuin-installer.sh"
[[ -x "$binary" && -f "$receipt" ]] || { printf '%s\n' 'Incomplete standalone Atuin installation.' >&2; exit 1; }
validate_receipt
printf '%s\n' 'Atuin installed. Open a new Zsh session; verify the client before enabling sync.'
