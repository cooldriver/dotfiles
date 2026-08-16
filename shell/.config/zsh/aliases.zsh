if command -v bat >/dev/null 2>&1; then
  alias cat='bat'
elif command -v batcat >/dev/null 2>&1; then
  alias cat='batcat'
fi

if command -v eza >/dev/null 2>&1; then
  alias lat='eza --all --long --sort=modified --reverse | head -n 10'
  alias lz='eza --color=always --long --git --no-filesize --icons=always --no-time --no-user --no-permissions'
fi

hpath() {
  print -l ${(s.:.)PATH} | sort
}
