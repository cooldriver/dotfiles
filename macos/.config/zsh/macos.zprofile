[[ -r "$HOME/.orbstack/shell/init.zsh" ]] && source "$HOME/.orbstack/shell/init.zsh"

# A default for new login shells only; direnv overrides this per project.
# Do not rewrite Homebrew links when entering or leaving a directory.
if [[ -x /opt/homebrew/opt/php@8.5/bin/php ]]; then
  path=(/opt/homebrew/opt/php@8.5/bin /opt/homebrew/opt/php@8.5/sbin $path)
fi
# Keep local launchers before commands installed by other integrations.
path=("$HOME/.local/bin" $path)
typeset -U path PATH
