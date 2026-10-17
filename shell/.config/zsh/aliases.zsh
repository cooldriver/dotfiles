if command -v bat >/dev/null 2>&1; then
  alias cat='bat'
elif command -v batcat >/dev/null 2>&1; then
  alias cat='batcat'
fi

if command -v eza >/dev/null 2>&1; then
  alias lz='eza --color=always --icons=always'
  alias lzl='lz --long --header --group-directories-first --color-scale=size --octal-permissions'
  alias lzr='lz --long --header --sort=modified --reverse --time-style=relative --color-scale=age'
  alias lzg='lz --long --header --all --git --group-directories-first'
  alias lzt='lz --tree --level=2'
fi

hpath() {
  print -l ${(s.:.)PATH} | sort
}
