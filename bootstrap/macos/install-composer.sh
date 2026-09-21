#!/bin/bash
set -euo pipefail

# Official release and SHA-256 from https://getcomposer.org/download/.
version=2.10.3
expected=7a2d379d5b8ffdaa028580ef26494c36d2feef4b178d3dd1473a4dbc5e17c8d6
target="${XDG_DATA_HOME:-$HOME/.local/share}/composer"
mkdir -p "$target"
temporary="$(mktemp "$target/.composer.XXXXXX")"
trap 'rm -f "$temporary"' EXIT

curl --fail --silent --show-error --location \
  "https://getcomposer.org/download/$version/composer.phar" --output "$temporary"
actual="$(shasum -a 256 "$temporary")"
actual="${actual%% *}"
if [[ "$actual" != "$expected" ]]; then
  printf '%s\n' 'Composer checksum mismatch; the installed PHAR was not changed.' >&2
  exit 1
fi
chmod 644 "$temporary"
mv -f "$temporary" "$target/composer.phar"
printf 'Installed Composer %s in %s\n' "$version" "$target"
