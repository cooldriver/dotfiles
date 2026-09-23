# Stationary Mac: private sync is available through the LAN/WireGuard route.
# Atuin 18.23.0 loads TOML after environment settings; select a dedicated file.
unset ATUIN_AUTO_SYNC ATUIN_SYNC_FREQUENCY
export ATUIN_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/atuin/hosts/tatooine"
