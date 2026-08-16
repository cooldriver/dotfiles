# Homebrew is installed in a different prefix on Apple Silicon and Intel Macs.
if [[ -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -x /usr/local/bin/brew ]]; then
  eval "$(/usr/local/bin/brew shellenv)"
fi

path=("$HOME/.local/bin" $path)
typeset -U path PATH

macos_profile="${XDG_CONFIG_HOME:-$HOME/.config}/zsh/macos.zprofile"
[[ -r "$macos_profile" ]] && source "$macos_profile"
