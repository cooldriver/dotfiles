# Atuin et fzf

Le paquet Stow `shell` initialise Atuin après fzf quand le binaire est disponible.

| Raccourci ou usage | Outil |
| --- | --- |
| `Ctrl+R` | Historique Atuin ; repli sur fzf si Atuin est absent |
| Flèche haut | Navigation habituelle de Zsh, sans interface Atuin |
| `Ctrl+T` | Sélection de fichiers fzf, avec aperçu bat si installé |
| `Alt+C` | Changement de répertoire fzf, avec aperçu eza si installé |
| `**` puis Tab | Complétion fzf pour les commandes prises en charge |
| Intégration Git | fzf-git si installé |
| Pipelines interactifs | Commande `fzf` toujours disponible |

Sur macOS, `Alt+C` nécessite que le terminal transmette Option comme Meta/Alt.
Les fichiers Zsh locaux chargés en fin de `.zshrc` peuvent modifier les raccourcis :
retirer toute ancienne initialisation Atuin/fzf en doublon.

## Activation

Installer Atuin (`brew install atuin` sur macOS), puis prévisualiser le déploiement
depuis la racine du dépôt :

```bash
stow --simulate --verbose --target "$HOME" shell
stow --restow --target "$HOME" shell
```

Si `~/.config/atuin/config.toml` existe, comparer et sauvegarder sa configuration
avant de résoudre le conflit Stow. Ouvrir ensuite un nouveau terminal. Importer
une fois l'historique Zsh existant, depuis ce terminal où `HISTFILE` est défini :

```bash
atuin import zsh
bindkey '^R'
bindkey '^T'
bindkey '^[c'
```

Résultats attendus : widget Atuin pour `Ctrl+R`, `fzf-file-widget` pour `Ctrl+T`,
`fzf-cd-widget` pour `Alt+C`. Tester aussi la flèche haut.

## Synchronisation privée par machine

La configuration partagée cible `https://atuin.hwapp.ovh`, prévu sur Gamorr.
Le serveur doit être déployé avant la création du compte. La configuration TOML
conserve `auto_sync = false` par défaut. Les fichiers Zsh par machine la surchargent
avec les variables d'environnement natives d'Atuin :

| Machine | Mode | Réglage Zsh |
| --- | --- | --- |
| Tatooine, Mac mini fixe sur le LAN | Automatique, intervalle de 5 minutes | `ATUIN_AUTO_SYNC=true`, `ATUIN_SYNC_FREQUENCY=5m` |
| Toola, MacBook mobile | Manuel, même lorsqu'il est sur le LAN | `ATUIN_AUTO_SYNC=false` |
| Autres machines | Manuel par défaut | Configuration TOML |

Les profils sont `shell/.config/zsh/hosts/tatooine.zsh` et `toola.zsh`.
Zsh normalise `hostname -s` en minuscules : `Tatooine` et `tatooine` sélectionnent
le même profil. Après déploiement Stow, ouvrir un nouveau terminal et vérifier
`hostname -s` puis `printenv ATUIN_AUTO_SYNC` (`true` sur Tatooine, `false` sur Toola).

Sur Tatooine, la synchronisation se déclenche à la fin d'une commande si le compte
est connecté et que l'intervalle est écoulé. Ce n'est pas un timer permanent :
aucune synchronisation périodique n'est garantie pendant l'inactivité du shell.
Les surcharges s'appliquent aux commandes lancées depuis ces sessions Zsh et à
leurs processus enfants ; un processus lancé indépendamment utilise le TOML.

`update_check = false` et le daemon désactivé restent communs aux deux postes.
Homebrew reste responsable des mises à jour du client. Sur Toola, aucune tentative
automatique de synchronisation n'est déclenchée, y compris hors VPN.

Après ouverture temporaire des inscriptions sur le serveur, depuis le LAN/VPN :

```bash
atuin register -u <username> -e <email>
atuin key
atuin sync
```

Saisir le mot de passe interactivement. Conserver la clé de chiffrement affichée
par `atuin key` dans le gestionnaire de mots de passe, puis fermer les inscriptions.
Sur les autres machines, configurer la même URL avant `atuin login -u <username>` ;
saisir le mot de passe et la même clé aux invites, puis lancer `atuin sync`.

Sur Toola hors VPN, l'enregistrement et la recherche restent locaux. Après
reconnexion, lancer `atuin sync` ; Toola ne rattrape pas automatiquement la
synchronisation. Tatooine se synchronise lors de l'utilisation du shell ;
`atuin sync` permet aussi de forcer un échange immédiat. Un appel manuel hors réseau
peut échouer explicitement, sans nouvelle tentative déclenchée par le shell.

Les bases, la clé et la session sous `~/.local/share/atuin` restent hors du dépôt.
La sauvegarde serveur contient l'historique chiffré et ne remplace pas la sauvegarde
de la clé client. Ne pas copier ce répertoire dans les dotfiles.

Sources : [raccourcis](https://docs.atuin.sh/latest/configuration/key-binding/),
[configuration](https://docs.atuin.sh/latest/configuration/config/).
