#!/bin/bash
set -euo pipefail

# This job is deliberately limited to Toola on its home LAN. No public probe.
export PATH="${PATH:-/usr/bin:/bin:/usr/sbin:/sbin}:/opt/homebrew/bin:/usr/local/bin"

[[ "$(hostname -s | tr '[:upper:]' '[:lower:]')" == toola ]] || exit 0

on_home_lan=false
for interface in $(ifconfig -l); do
  case "$interface" in
    en[0-9]*) ;;
    *) continue ;;
  esac
  address="$(ipconfig getifaddr "$interface" 2>/dev/null)" || continue
  if [[ "$address" == 10.0.1.34 || "$address" == 10.0.1.35 ]]; then
    on_home_lan=true
    break
  fi
done
[[ "$on_home_lan" == true ]] || exit 0

# Require split DNS, and reject a mixed private/public result. In particular,
# this skips the VPN setup that currently resolves the public Gamorr address.
addresses="$(dscacheutil -q host -a name atuin.hwapp.ovh | awk '$1 == "ip_address:" { print $2 }')" || exit 0
[[ -n "$addresses" ]] || exit 0
while IFS= read -r address; do
  [[ "$address" == 10.0.30.100 ]] || exit 0
done <<< "$addresses"

# Pin the connection to the private IP even if DNS changes after the check.
# Keep TLS certificate verification and the hostname; never probe public Gamorr.
curl --fail --silent --output /dev/null --noproxy '*' \
  --connect-timeout 3 --max-time 8 \
  --resolve atuin.hwapp.ovh:443:10.0.30.100 \
  https://atuin.hwapp.ovh/ || exit 0

# launchd does not load interactive Zsh startup files. Use Toola's common,
# manual-sync configuration and the existing user session/key, not root's.
export ATUIN_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/atuin"
if ! command -v atuin >/dev/null 2>&1; then
  logger -t toola-atuin-sync 'atuin executable not found'
  exit 1
fi
if ! atuin sync; then
  logger -t toola-atuin-sync 'atuin sync failed on the home LAN'
  exit 1
fi
