# Servers with permanent access to the private Atuin endpoint; opt in with Stow.
# Local and host files loaded later by .zshrc can override this profile.
unset ATUIN_AUTO_SYNC ATUIN_SYNC_FREQUENCY
export ATUIN_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/atuin/profiles/linux-server"
