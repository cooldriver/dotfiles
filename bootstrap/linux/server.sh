#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
source "$script_dir/common.sh"

main() {
  prepare_apt
  install_common_packages
  install_required rsync unzip lsof dnsutils ncdu tree python3
  bash "$script_dir/install-atuin.sh"
  install_shell_dependencies
}

main "$@"
