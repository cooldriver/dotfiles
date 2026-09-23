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

Dans Zellij, le mode normal et les raccourcis affichés par l'interface sont
actifs dès le démarrage : `Ctrl+P` pour les panneaux, `Ctrl+T` pour les onglets,
`Ctrl+R` pour le redimensionnement et `Ctrl+O` pour les sessions. La flèche haut
ouvre l'historique Atuin dans Zsh si Atuin est installé. `Ctrl+G` passe
temporairement en mode verrouillé
pour transmettre les raccourcis à une application dans un panneau.
Pour quitter le terminal sans terminer le travail, utiliser `Ctrl+O`, puis
`d` pour détacher la session. La fermeture forcée du terminal
détache aussi la session ; ce comportement ne remplace pas une sauvegarde ni
une restauration des processus après redémarrage du serveur.

Pour conserver un travail **sur un serveur**, se connecter en SSH, démarrer
Zellij sur ce serveur, puis rattacher sa session depuis une connexion ultérieure.
Une session Zellij lancée uniquement sur le Mac ne maintient pas à elle seule
les processus distants après la coupure SSH. Éviter d'imbriquer deux sessions
Zellij (Mac et serveur) tant que les raccourcis imbriqués n'ont pas été validés.

Tester sur chaque terminal la copie, les couleurs, la flèche haut et la reprise après
une déconnexion SSH avant d'abandonner les sessions tmux existantes. L'installation
ne supprime pas tmux déjà présent et ne migre pas ses sessions.
