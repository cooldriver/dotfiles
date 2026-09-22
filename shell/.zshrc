[[ -o interactive ]] || return

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

if command -v fzf >/dev/null 2>&1; then
  eval "$(fzf --zsh)"

  if command -v fd >/dev/null 2>&1; then
    fd_command=fd
  elif command -v fdfind >/dev/null 2>&1; then
    fd_command=fdfind
  else
    fd_command=''
  fi

  if [[ -n "$fd_command" ]]; then
    export FZF_DEFAULT_COMMAND="$fd_command --hidden --strip-cwd-prefix --exclude .git"
    export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
    export FZF_ALT_C_COMMAND="$fd_command --type=d --hidden --strip-cwd-prefix --exclude .git"

    _fzf_compgen_path() {
      "$fd_command" --hidden --exclude .git . "$1"
    }

    _fzf_compgen_dir() {
      "$fd_command" --type=d --hidden --exclude .git . "$1"
    }
  fi

  if command -v bat >/dev/null 2>&1; then
    export FZF_CTRL_T_OPTS='--preview "bat -n --color=always --line-range :500 {}"'
  elif command -v batcat >/dev/null 2>&1; then
    export FZF_CTRL_T_OPTS='--preview "batcat -n --color=always --line-range :500 {}"'
  fi

  if command -v eza >/dev/null 2>&1; then
    export FZF_ALT_C_OPTS='--preview "eza --tree --color=always {}"'
  fi
fi

fzf_git="$HOME/.local/share/fzf-git/fzf-git.sh"
[[ -r "$fzf_git" ]] && source "$fzf_git"

# Atuin owns Ctrl-R when installed; fzf keeps Ctrl-T, Alt-C and completion.
# Initialize after fzf so its history binding is replaced in each keymap.
# Without Atuin, fzf's Ctrl-R remains available. Keep native up-arrow history.
if command -v atuin >/dev/null 2>&1; then
  eval "$(atuin init zsh --disable-up-arrow)"
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
