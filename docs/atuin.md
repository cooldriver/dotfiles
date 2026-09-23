# Atuin

Le paquet Stow `shell` initialise Atuin quand le binaire est disponible.

| Raccourci ou usage | Outil |
| --- | --- |
| Flèche haut | Historique Atuin si installé ; sinon, historique habituel de Zsh |
| `Ctrl+R` | Recherche historique standard de Zsh hors de Zellij ; mode redimensionnement dans Zellij |
| `Ctrl+T` | Mode onglets dans Zellij |
| Navigation entre répertoires | `zoxide` si installé, avec `z` |
| Navigation Git interactive | Lazygit, lancé à la demande |

Les fichiers Zsh locaux chargés en fin de `.zshrc` peuvent modifier les raccourcis :
retirer toute ancienne initialisation Atuin en doublon.

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
bindkey '^[[A'
bindkey '^[OA'
bindkey '^R'
```

Résultats attendus : widget Atuin pour la flèche haut ; hors de Zellij,
`Ctrl+R` utilise la recherche habituelle de Zsh. Dans Zellij, le mode normal
reçoit `Ctrl+R` et `Ctrl+T` avant Zsh ; vérifier la flèche haut.
Atuin modifie donc l'usage de la flèche haut : elle ouvre la recherche d'historique
au lieu de parcourir directement les commandes précédentes.

## Synchronisation privée par machine

La configuration partagée cible `https://atuin.hwapp.ovh`, prévu sur Gamorr.
Le serveur doit être déployé avant la création du compte. La configuration TOML
conserve `auto_sync = false` par défaut. Les profils Zsh sélectionnent le dossier
de configuration avec `ATUIN_CONFIG_DIR` :

| Machine | Mode | Réglage Zsh |
| --- | --- | --- |
| Tatooine, Mac mini fixe sur le LAN | Automatique, intervalle de 5 minutes | `~/.config/atuin/hosts/tatooine/config.toml` |
| Toola, MacBook mobile | Manuel, même lorsqu'il est sur le LAN | `~/.config/atuin/config.toml` |
| Autres machines | Manuel par défaut | Configuration TOML |

Les profils sont `shell/.config/zsh/hosts/tatooine.zsh` et `toola.zsh`.
Zsh normalise `hostname -s` en minuscules : `Tatooine` et `tatooine` sélectionnent
le même profil. Après déploiement Stow, ouvrir un nouveau terminal et vérifier
`hostname -s`, `printenv ATUIN_CONFIG_DIR` puis `atuin config get auto_sync --resolved`
(`true` sur Tatooine, `false` sur Toola). Les chemins respectent `XDG_CONFIG_HOME`
s'il est défini.

Dans Atuin 18.23.0, le TOML est chargé après les variables `ATUIN_AUTO_SYNC` et
`ATUIN_SYNC_FREQUENCY` : les valeurs du fichier les écrasent. L'ancien mécanisme
par variables n'activait donc pas la synchronisation sur Tatooine. Les profils
retirent ces anciennes variables et sélectionnent désormais un fichier complet.
`ATUIN_CONFIG_DIR` ne change ni les bases, ni la clé, ni la session existante :
aucune reconnexion ou réimportation n'est nécessaire. Maintenir les réglages
communs dans les deux fichiers TOML lors de leurs prochaines modifications.

Sur Tatooine, la synchronisation se déclenche à la fin d'une commande si le compte
est connecté et que l'intervalle est écoulé. Ce n'est pas un timer permanent :
aucune synchronisation périodique n'est garantie pendant l'inactivité du shell.
La sélection s'applique aux commandes lancées depuis ces sessions Zsh et à
leurs processus enfants ; un processus indépendant sans `ATUIN_CONFIG_DIR`
utilise le fichier manuel par défaut.

Pour contrôler les valeurs réellement appliquées et l'état de synchronisation :

```bash
atuin config get auto_sync --resolved
atuin config get sync_frequency --resolved
atuin status
```

Sur Tatooine, les valeurs attendues sont `true` et `5m`. Dans la version 18.23.0,
`atuin status` n'affiche la fréquence, la dernière synchronisation et les détails
distants que lorsque `auto_sync` est activé. Une sortie limitée à `[Local]` sur
Toola est donc normale. `atuin sync` permet un contrôle manuel de l'échange.

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
