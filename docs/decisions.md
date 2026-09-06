# Décisions de conception

Ce document consigne les choix validés avant la création des dotfiles. Il sert
de référence pendant la mise en place et les futures réinstallations.

## Périmètre

- Dépôt GitHub public : aucun secret, clé privée, jeton, mot de passe ou donnée
  confidentielle ne doit y être ajouté.
- Cibles : macOS, serveurs Ubuntu, Debian/Proxmox et Raspberry Pi OS. Un Linux
  desktop pourra être ajouté plus tard.
- GNU Stow reste le mécanisme de déploiement. La structure initialement
  attendue par le runbook homelab est conservée.
- Les fichiers communs seront déployés sur toutes les machines. Les réglages
  macOS seront groupés dans un paquet Stow `macos` déployé seulement sur macOS.

## Structure envisagée

```text
shell/.zshrc
shell/.zprofile
shell/.config/zsh/aliases.zsh
git/.gitconfig
vim/.vimrc
btop/.config/btop/btop.conf
macos/.config/zsh/macos.zprofile
brew/Brewfile
```

`brew` ne sera pas déployé dans le home avec Stow. Neovim sera réalisé dans une
phase distincte. La structure finale restera minimale et ne contiendra que les
fichiers effectivement utilisés.

## Zsh

- Zsh est le shell commun à toutes les machines.
- La configuration sera personnelle, courte et non dérivée du template Oh My
  Zsh.
- Powerlevel10k est retiré. Spaceship sera installé par clone Git explicite sur
  macOS et Linux, puis chargé par Oh My Zsh.
- Les intégrations optionnelles (`fzf`, `fd`, `eza`, `bat`, `zoxide`, NVM,
  fzf-git) testeront la présence de leur commande ou fichier avant chargement.
- Les alias et petites fonctions seront séparés dans
  `~/.config/zsh/aliases.zsh`.
- `bat` remplacera `cat`. `cd` ne sera pas remplacé par `zoxide`.
- `broot`, les anciens chemins DBngin/MySQL et `ansible@10` ne seront pas
  repris dans la configuration shell. DBngin et Ansible restent installés sur
  macOS via le Brewfile.
- Les réglages locaux et les secrets seront hors Git. Lorsqu'un fichier local
  est nécessaire, il sera chargé seulement s'il est lisible.
- L'intégration OrbStack sera versionnée dans le paquet `macos`, avec un
  chargement conditionnel si OrbStack est installé.

## Git et SSH

- Git utilisera Delta comme pager et outil de diff interactif. La fonction
  shell `diff_fancy` ne sera pas reprise.
- Les commits seront signés avec le format de signature SSH et
  `commit.gpgsign = true`.
- La configuration spécifique à 1Password ne sera pas placée dans la
  configuration commune pendant la migration vers Proton Pass.
- Les identités personnelle et professionnelle seront sélectionnées par
  `includeIf` selon le répertoire des dépôts. Leurs fichiers locaux resteront
  hors Git tant que leurs valeurs ne sont pas explicitement considérées comme
  publiques.
- Les deux comptes GitHub utiliseront SSH, avec un alias d'hôte distinct par
  identité et une clé privée distincte. Les clés privées ne sont jamais
  versionnées.
- Les alias Git reposant sur `assume-unchanged` ne seront pas repris par
  défaut.
- Les répertoires cibles sont `~/Developer/personal/` pour les dépôts
  personnels et `~/Developer/work/` pour les dépôts professionnels. Cette
  règle est destinée aux nouvelles installations ; aucun déploiement n'est
  effectué sur la machine actuelle.

## Éditeurs

- Vim restera disponible sur les serveurs avec une configuration minimale,
  sans plugin obligatoire : coloration, types de fichiers, indentation,
  numéros de ligne et améliorations visuelles essentielles.
- Neovim aura une configuration indépendante en Lua, construite plus tard à
  partir de besoins concrets.
- VS Code est hors périmètre pour le moment.

## tmux

- tmux fait partie des outils installés sur les machines, mais aucune
  configuration ne sera versionnée initialement.
- Un paquet `tmux` ne sera ajouté qu'après l'identification de raccourcis ou
  comportements réels à conserver.

## btop

- Le fichier généré complet ne sera pas repris.
- La future configuration sera minimale et portable, sans chemin Homebrew ni
  thème dépendant d'une version installée.
- `save_config_on_exit = false` évitera que btop modifie le fichier versionné à
  travers son lien Stow.

## Homebrew

- `brew/Brewfile` est la source de référence pour les installations macOS.
- Il est appliqué avec `brew bundle --file brew/Brewfile` depuis la racine du
  dépôt, après installation de Homebrew.
- Les sections et commentaires utiles sont conservés. Les paquets désactivés,
  reliquats historiques et doublons sont retirés.

## Bootstrap Linux

- `bootstrap/linux/common.sh` installe les dépendances terminal communes aux
  dotfiles sur les distributions basées sur Debian.
- `bootstrap/linux/server.sh` ajoute les outils d’administration utilisés dans
  le homelab. Le runbook appelle ce profil après le clonage du dépôt.
- Un profil desktop sera ajouté plus tard, sans imposer d’applications
  graphiques aux serveurs.
