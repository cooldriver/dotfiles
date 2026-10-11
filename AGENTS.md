# Repository guidance for coding agents

This is a personal, public dotfiles repository. Make small, reviewable changes;
do not turn it into a generic dotfiles framework.

## Layout and deployment

- GNU Stow deploys `shell`, `git`, `vim`, `btop`, `zellij`, and `lazygit` on
  macOS and Linux. Deploy `macos` only on macOS.
- `brew`, `bootstrap`, `docs`, `services`, `scripts`, and `tests` are not Stow packages.
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

## Shared quality baseline

- Fieldbook owns personal workflows and operational runbooks; this repository owns configuration, code, tests, and development documentation.
- Read relevant implementations and tests before editing. Prefer the smallest correct change; preserve optional integrations, shell compatibility, and the public repository's existing documentation language.
- Install the pinned Python linter from `requirements-dev.txt` in an isolated environment. Run `python -m ruff check --no-cache .`, `bash scripts/check-shell.sh`, and `python -B scripts/check-tests.py`. Ruff checks common errors only, without formatting or a configured type checker. ShellCheck covers Bash, not Zsh; the shared script checks Zsh syntax without sourcing it.
- Add regression tests for bugs and useful tests for changed behavior, errors, and preservation of existing files. Keep tests offline, with synthetic credentials and temporary homes; do not weaken assertions to hide defects.
- One existing identity test runs `git init` in a temporary repository. `scripts/check-tests.py` excludes exactly `test_git_personal_identity_is_default_and_work_overrides_it` under the Git rule above and reports it; CI retains the full suite. Agents use this runner locally. Never claim a full local pass when it was excluded.
- CI checks Ubuntu and macOS but does not validate real Debian deployment, Homebrew bootstrap, service activation, or a user's actual environment. Report skipped optional tests separately.

## Independent review and completion

After initial validation, use `.opencode/agents/reviewer.md` for significant shell logic, bootstrap/deployment, credentials, Git-account helpers, services, cross-platform changes, meaningful bug fixes, or risky refactors. Self-review is sufficient for trivial documentation or comments.

Provide the request, expected behavior, files/diff, untracked files, and validation results. The reviewer reads only and does not run tests. Assess findings independently, fix confirmed Critical/Major issues, handle Minor suggestions proportionately, add regressions, and rerun affected checks. At most one targeted follow-up review after substantial corrections; the reviewer must not delegate recursively.

If the project reviewer is unavailable, an available subagent may apply its prompt in read-only mode; disclose the fallback. Without delegation, self-review and explicitly report the absence of independent review.

A task is complete when the intended behavior is supported by relevant tests and configured checks, or limitations are explicit, with focused changes and updated documentation. Finish with actual validation results, exclusions/skips, review mode, and remaining issues. Local checks do not prove a GitHub run or real deployment succeeded.
