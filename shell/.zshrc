[[ -o interactive ]] || return

export LG_CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/lazygit/config.yml"

export ZSH="$HOME/.oh-my-zsh"

if [[ -r "$ZSH/oh-my-zsh.sh" ]]; then
  plugins=(git)

  if [[ -r "$ZSH/custom/themes/spaceship.zsh-theme" ]]; then
    ZSH_THEME="spaceship"
  else
    ZSH_THEME=""
  fi

  source "$ZSH/oh-my-zsh.sh"
fi

if command -v direnv >/dev/null 2>&1; then
  eval "$(direnv hook zsh)"
fi

# Atuin owns Up when installed; Zellij handles Ctrl-R and Ctrl-T in its normal mode.
if command -v atuin >/dev/null 2>&1; then
  eval "$(atuin init zsh --disable-ctrl-r)"
fi

if command -v zoxide >/dev/null 2>&1; then
  eval "$(zoxide init zsh)"
fi

export NVM_DIR="$HOME/.nvm"
if [[ -s "$NVM_DIR/nvm.sh" ]]; then
  source "$NVM_DIR/nvm.sh"
elif command -v brew >/dev/null 2>&1; then
  nvm_script="$(brew --prefix nvm 2>/dev/null)/nvm.sh"
  [[ -s "$nvm_script" ]] && source "$nvm_script"
fi

aliases_file="${XDG_CONFIG_HOME:-$HOME/.config}/zsh/aliases.zsh"
[[ -r "$aliases_file" ]] && source "$aliases_file"

local_config="${XDG_CONFIG_HOME:-$HOME/.config}/zsh/local.zsh"
[[ -r "$local_config" ]] && source "$local_config"

host_name="$(hostname -s)"
host_config="${XDG_CONFIG_HOME:-$HOME/.config}/zsh/hosts/${host_name:l}.zsh"
[[ -r "$host_config" ]] && source "$host_config"

# Load last so it can inspect the final command line editor configuration.
syntax_highlighting=""
if command -v brew >/dev/null 2>&1; then
  syntax_highlighting="$(brew --prefix zsh-syntax-highlighting 2>/dev/null)/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
elif [[ -r /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]]; then
  syntax_highlighting=/usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
fi
[[ -r "$syntax_highlighting" ]] && source "$syntax_highlighting"
