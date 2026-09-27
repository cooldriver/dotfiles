# Atuin

Le paquet Stow `shell` initialise Atuin quand le binaire est disponible.

| Raccourci ou usage | Outil |
| --- | --- |
| Flèche haut | Parcours de l'historique Zsh |
| `Ctrl+R` | Recherche Atuin si installé ; sinon, recherche habituelle de Zsh, y compris dans Zellij en mode normal |
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

Résultats attendus : `Ctrl+R` ouvre la recherche Atuin, y compris dans Zellij
en mode normal ; la flèche haut parcourt les commandes précédentes dans Zsh.
Zellij réserve `Ctrl+N` au mode redimensionnement et `Ctrl+T` au mode onglets.
Les réglages locaux de Zsh ou du terminal peuvent modifier ces raccourcis.

## Synchronisation privée par machine

La configuration partagée cible `https://atuin.hwapp.ovh`, prévu sur Gamorr.
Le serveur doit être déployé avant la création du compte. La configuration TOML
conserve `auto_sync = false` par défaut. Les profils Zsh sélectionnent le dossier
de configuration avec `ATUIN_CONFIG_DIR` :

| Machine | Mode | Réglage Zsh |
| --- | --- | --- |
| Tatooine, Mac mini fixe sur le LAN | Automatique, intervalle de 5 minutes | `~/.config/atuin/hosts/tatooine/config.toml` |
| Toola, MacBook mobile | Manuel dans Zsh ; LaunchAgent optionnel uniquement sur le LAN | `~/.config/atuin/config.toml` |
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
automatique n'est déclenchée par Zsh ; le LaunchAgent décrit ci-dessous ne tente
une synchronisation que sur le LAN.

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

Sur Toola hors LAN, l'enregistrement et la recherche restent locaux. Au retour
sur le LAN, le LaunchAgent optionnel rattrape la synchronisation à son prochain
passage si le Mac est éveillé. Tatooine se synchronise lors de l'utilisation
du shell ; `atuin sync` permet aussi de forcer un échange immédiat sur une
connexion fonctionnelle. Un appel manuel hors réseau peut échouer explicitement.

### Synchronisation locale optionnelle sur Toola

Le dépôt fournit `services/macos/toola-atuin-sync.sh` et son LaunchAgent dans
`services/macos/`. **Ils ne sont pas installés par Stow ni activés par le
bootstrap commun.** L'installateur refuse toute autre machine que Toola et
refuse de remplacer un fichier cible différent. Sur Toola uniquement :

```bash
bash bootstrap/macos/install-toola-atuin-sync.sh
launchctl print "gui/$(id -u)/com.fieldbook.toola-atuin-sync"
```

Le job est exécuté sous le compte utilisateur environ toutes les cinq minutes
quand sa session est ouverte et que macOS le réveille ; ce n'est pas une
garantie de cadence pendant la veille. Le script exige le nom d'hôte `toola`,
l'adresse Ethernet `10.0.1.34` ou Wi-Fi `10.0.1.35` sur une interface `en*`,
et une résolution système **uniquement** vers `10.0.30.100` pour
`atuin.hwapp.ovh`. Il teste alors HTTPS avec validation TLS, en épinglant cette
adresse privée pour ne jamais interroger l'IP publique, puis lance `atuin sync`
avec la configuration manuelle du compte. Sans ces conditions, il sort sans
faire de requête vers Gamorr. Sur VPN depuis l'extérieur, Toola résout ce nom
vers l'IP publique : aucune synchronisation automatique n'est prévue.

Pour tester : depuis le LAN, vérifier `dscacheutil -q host -a name atuin.hwapp.ovh`
(résultat attendu : `10.0.30.100`), puis exécuter
`~/.local/bin/toola-atuin-sync` et contrôler la synchronisation sur l'autre
poste. Hors LAN, exécuter le même script et vérifier qu'aucune tentative de
synchro n'a lieu. Les échecs d'Atuin sont signalés avec le tag
`toola-atuin-sync` dans les journaux système ; les indisponibilités de réseau
sont silencieuses. Le LaunchAgent ne lance pas deux instances du même job
simultanément. Une mise à jour du script ou du plist déjà installé nécessite
de comparer les copies locales, de décharger le job avec `launchctl bootout`,
de remplacer les fichiers après sauvegarde si nécessaire, puis de relancer
l'installateur. Pour arrêter le job sans supprimer les données Atuin :

```bash
launchctl bootout "gui/$(id -u)/com.fieldbook.toola-atuin-sync"
```

Les bases, la clé et la session sous `~/.local/share/atuin` restent hors du dépôt.
La sauvegarde serveur contient l'historique chiffré et ne remplace pas la sauvegarde
de la clé client. Ne pas copier ce répertoire dans les dotfiles.

Sources : [raccourcis](https://docs.atuin.sh/latest/configuration/key-binding/),
[configuration](https://docs.atuin.sh/latest/configuration/config/).
