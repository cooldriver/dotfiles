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

## Mise à jour et retour

Sur macOS, la version gérée par Homebrew se met à jour avec `brew upgrade zellij`. Sur Linux, le binaire installé par ce dépôt n'est pas géré par APT et ne fournit pas de commande d'auto-mise à jour équivalente à `atuin update`. Aucun timer de mise à jour n'est ajouté.

Pour changer de version sous Linux, réviser `version` et les deux empreintes **des archives `.tar.gz`** dans `bootstrap/linux/install-zellij.sh` à partir des assets officiels, vérifier les téléchargements puis tester et publier la modification. Les fichiers upstream `.sha256sum` de cette release décrivent les **binaires extraits**, pas les archives : ne pas les utiliser directement pour vérifier un `.tar.gz`. Une empreinte incorrecte arrête l'installation avec un message explicite, sans extraire ni exécuter le téléchargement ou remplacer le lien existant.

Après récupération de la mise à jour du dépôt sur chaque machine concernée, relancer uniquement l'installateur, sans réexécuter tout le bootstrap système :

```sh
bash ~/src/dotfiles/bootstrap/linux/install-zellij.sh
~/.local/bin/zellij --version
```

L'installateur conserve les versions précédentes sous `~/.local/opt/zellij/` et fait pointer `~/.local/bin/zellij` vers la version sélectionnée. Le relancer pour une version déjà installée ne télécharge rien et ne vérifie pas à nouveau son binaire. Tester une nouvelle session avant de retirer une ancienne version ; les sessions déjà ouvertes ne sont pas mises à niveau par le changement du lien. Pour revenir en arrière, vérifier que le binaire de la version précédente existe et réorienter ce seul lien vers lui, sans supprimer les versions ni la configuration.

## Utilisation

```bash
zellij --version
zellij --session travail
zellij list-sessions
zellij attach travail
```

Dans Zellij, le mode normal et les raccourcis affichés par l'interface sont
actifs dès le démarrage : `Ctrl+P` pour les panneaux, `Ctrl+T` pour les onglets,
`Ctrl+N` pour le redimensionnement et `Ctrl+O` pour les sessions. `Ctrl+R`
est transmis à Zsh pour ouvrir la recherche Atuin si elle est installée ;
la flèche haut parcourt l'historique Zsh. `Ctrl+G` passe
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
