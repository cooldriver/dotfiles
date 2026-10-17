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
  if (( $# > 1 )) || { (( $# == 1 )) && [[ "$1" != --ordered ]]; }; then
    print -u2 -r -- 'Usage: hpath [--ordered]'
    return 2
  fi

  local -a entries=()
  local entry
  local -i i
  for (( i = 1; i <= ${#path}; i++ )); do
    printf -v entry '%3d\t%s' "$i" "${path[i]}"
    entries+=("$entry")
  done
  (( ${#entries} )) || return 0

  if (( $# == 0 )); then
    print -rl -- "${entries[@]}" | sort -s -t $'\t' -k2
  else
    print -rl -- "${entries[@]}"
  fi
}
