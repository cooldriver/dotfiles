#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 || ( "$1" != --check && "$1" != --apply ) ]]; then
  printf '%s\n' 'Usage: timemachine.sh --check|--apply EXCLUSIONS_FILE' >&2
  exit 2
fi
mode="$1"
list="$2"
if [[ ! -r "$list" ]]; then
  printf 'Cannot read exclusions: %s\n' "$list" >&2
  exit 1
fi

# Parse the entire file before changing anything. Do not evaluate shell input.
paths=()
while IFS= read -r item || [[ -n "$item" ]]; do
  case "$item" in
    ''|\#*) continue ;;
    \~/*) item="$HOME/${item#\~/}" ;;
    /*) ;;
    *) printf 'Expected an absolute path or ~/path: %s\n' "$item" >&2; exit 1 ;;
  esac
  case "$item" in
    *'*'*|*'?'*|*'['*|*'$'*|*$'\r'*|*/../*|*/..|*/./*|*/.|*/)
      printf 'Use a literal normalized path without a trailing slash: %s\n' "$item" >&2
      exit 1 ;;
  esac
  if [[ "$item" == "$HOME" ]]; then
    printf '%s\n' 'Refusing to exclude the entire home directory.' >&2
    exit 1
  fi
  paths+=("$item")
done < "$list"

if [[ ${#paths[@]} -eq 0 ]]; then
  printf '%s\n' 'No exclusions listed.'
  exit 0
fi

for item in "${paths[@]}"; do
  if [[ "$mode" == --apply ]]; then
    sudo tmutil addexclusion -p "$item"
  fi
  if [[ -e "$item" ]]; then
    tmutil isexcluded "$item"
  else
    printf 'Absent path (mode %s): %s\n' "$mode" "$item"
  fi
done
