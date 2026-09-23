#!/usr/bin/env bash

set -euo pipefail

# Upstream Linux musl releases; keep the archive hashes in sync with the version.
version=0.45.1
case "$(uname -m)" in
  x86_64)
    arch=x86_64
    checksum=d7bda1e18c30a688833ae7627f1d6a253bbba5349a4bc48e4f0ec008aaf75ed1
    ;;
  aarch64|arm64)
    arch=aarch64
    checksum=05f0802afadd53f8db9514e7cae53c9ae8432fed1b35b8294aa816ee3044a16b
    ;;
  *)
    printf 'Unsupported Zellij architecture: %s\n' "$(uname -m)" >&2
    exit 1
    ;;
esac

if [[ $(uname -s) != Linux ]]; then
  printf '%s\n' 'This installer is for Linux only.' >&2
  exit 1
fi

install_dir="$HOME/.local/opt/zellij/v$version"
binary="$install_dir/zellij"
link="$HOME/.local/bin/zellij"

if [[ -e "$link" || -L "$link" ]]; then
  if [[ ! -L "$link" || $(readlink "$link") != "$HOME/.local/opt/zellij/"*/zellij ]]; then
    printf 'Refusing to replace an unmanaged Zellij binary: %s\n' "$link" >&2
    exit 1
  fi
fi

if [[ ! -x "$binary" ]]; then
  archive="zellij-$arch-unknown-linux-musl.tar.gz"
  url="https://github.com/zellij-org/zellij/releases/download/v$version/$archive"
  tmp=$(mktemp -d)
  trap 'rm -rf -- "$tmp"' EXIT
  curl --fail --location --retry 3 --output "$tmp/$archive" "$url"
  printf '%s  %s\n' "$checksum" "$tmp/$archive" | sha256sum --check --status
  tar -xzf "$tmp/$archive" -C "$tmp" zellij
  mkdir -p "$install_dir"
  install -m 755 "$tmp/zellij" "$binary"
fi

mkdir -p "$(dirname "$link")"
ln -sfn "$binary" "$link"
"$binary" --version
