# Zellij sur macOS et Linux

Zellij remplace tmux comme multiplexeur interactif. Son démarrage reste manuel :
une connexion SSH, un shell non interactif et une tâche automatisée n'ouvrent
jamais de session implicitement.

## Installation

- macOS : `brew bundle install --file brew/Brewfile` installe `zellij`.
- Debian, Ubuntu et Raspberry Pi OS 64 bits : `bootstrap/linux/server.sh`
  installe un binaire officiel Linux dans `~/.local/opt/zellij/v0.45.1/` et
  crée `~/.local/bin/zellij`. `bootstrap/linux/common.sh` fait de même.
  L'archive est vérifiée avec les SHA-256 fixés dans
  `bootstrap/linux/install-zellij.sh` ; ce script peut être relancé. Seules les
  architectures `x86_64` et `aarch64` sont prises en charge. Sur un Raspberry Pi
  OS 32 bits, ne pas lancer ce profil avant d'avoir choisi un mode d'installation
  adapté. Pour changer de version, réviser ensemble la version et les deux
  sommes de contrôle à partir de la publication officielle.

Vérifier que `~/.local/bin` est dans le PATH (le paquet `shell` le prévoit), puis
prévisualiser `stow --simulate --verbose --target "$HOME" zellij`. Comparer et
sauvegarder toute configuration préexistante avant `stow --target "$HOME" zellij`.
La configuration commune vit dans `zellij/.config/zellij/config.kdl`.

## Utilisation

```bash
zellij --version
zellij --session travail
zellij list-sessions
zellij attach travail
```

Dans Zellij, `Ctrl+G` quitte le mode verrouillé pour donner accès aux raccourcis
affichés par l'interface (`Ctrl+P` pour les panneaux, `Ctrl+T` pour les onglets,
`Ctrl+O` pour les sessions). `Ctrl+G` revient au mode verrouillé : les touches
du shell, dont `Ctrl+R` pour Atuin/fzf, sont alors transmises normalement.
`Ctrl+G` reste réservé à Zellij, même en mode verrouillé : fzf-git n'est plus
chargé dans le shell ; Lazygit assure la navigation Git interactive.
Pour quitter le terminal sans terminer le travail, utiliser `Ctrl+G`, puis
`Ctrl+O`, puis `d` pour détacher la session. La fermeture forcée du terminal
détache aussi la session ; ce comportement ne remplace pas une sauvegarde ni
une restauration des processus après redémarrage du serveur.

Pour conserver un travail **sur un serveur**, se connecter en SSH, démarrer
Zellij sur ce serveur, puis rattacher sa session depuis une connexion ultérieure.
Une session Zellij lancée uniquement sur le Mac ne maintient pas à elle seule
les processus distants après la coupure SSH. Éviter d'imbriquer deux sessions
Zellij (Mac et serveur) tant que les raccourcis imbriqués n'ont pas été validés.

Tester sur chaque terminal la copie, les couleurs, `Ctrl+R` et la reprise après
une déconnexion SSH avant d'abandonner les sessions tmux existantes. L'installation
ne supprime pas tmux déjà présent et ne migre pas ses sessions.
