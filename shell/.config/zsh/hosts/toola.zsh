# Mobile Mac: no shell auto-sync; an optional LAN-only LaunchAgent syncs separately.
unset ATUIN_AUTO_SYNC ATUIN_SYNC_FREQUENCY
export ATUIN_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/atuin"
