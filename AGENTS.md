# Repository guidance for coding agents

This is a personal, public dotfiles repository. Make small, reviewable changes;
do not turn it into a generic dotfiles framework.

## Layout and deployment

- GNU Stow deploys `shell`, `git`, `vim`, `btop`, `zellij`, and `lazygit` on
  macOS and Linux. Deploy `macos` only on macOS.
- `brew`, `bootstrap`, `docs`, `services`, and `tests` are not Stow packages.
- Keep Zsh as the shared shell. Follow the existing package layout and make
  integrations optional when the underlying command is not installed.
- Keep installation and service activation explicit and reviewable.
- Keep host-specific settings and credentials out of shared Stow packages.
  See `README.md` for the supported local files.

## Safety

- Never commit secrets, private keys, tokens, passwords, or confidential data.
  Git identity files and SSH configuration belong outside this repository.
- Do not deploy with Stow into the real home directory or run bootstrap scripts
  as a validation step. Use temporary directories and simulations instead.
- Do not run Git commands that modify the working tree, index, references, or
  remotes. Leave staging, commits, and publishing to the owner.

## Changes and checks

- Keep `README.md` and relevant guides in sync with behavior changes.
- Update `AGENTS.md` when repository conventions, safety rules, or validation
  practices change; it does not need an edit for every configuration change.
- For shell changes, use `zsh -n` or `bash -n` as appropriate. Run the offline
  tests with `python3 -m unittest discover -s tests` when relevant.
- For Stow layout changes, preview with `stow --simulate --verbose --dir .
  --target <temporary-home> <packages>`; resolve conflicts rather than forcing
  links over existing files.
- Check `git diff --check` before handing changes back for review.
