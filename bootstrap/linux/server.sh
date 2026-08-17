#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
source "$script_dir/common.sh"

main() {
  prepare_apt
  install_common_packages
  install_required rsync unzip lsof dnsutils ncdu tree
  install_shell_dependencies
}

main "$@"
