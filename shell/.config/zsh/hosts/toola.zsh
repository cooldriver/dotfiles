# Mobile Mac: sync explicitly with `atuin sync` when LAN/VPN is available.
unset ATUIN_AUTO_SYNC ATUIN_SYNC_FREQUENCY
export ATUIN_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/atuin"
