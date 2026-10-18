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
| Serveurs Linux avec le module Stow `linux-server` | Automatique, intervalle de 5 minutes d'activité du shell | `~/.config/atuin/profiles/linux-server/config.toml` |
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
communs dans les trois fichiers TOML lors de leurs prochaines modifications.

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

### Serveurs Linux

Le bootstrap `bootstrap/linux/server.sh` installe le client autonome officiel, pas le paquet APT : le client Debian 13 `18.6.1` a échoué sur les enregistrements récents du compte partagé lors du pilote kiros le 2026-10-18. Le client officiel `18.24.1` a ensuite synchronisé et permis de reconstruire l'historique local. Linux x86_64 et arm64 sont officiellement Tier 1 ; l'installateur sélectionne la cible adaptée, les binaires GNU de cette release demandant glibc >= 2.39 (Debian 13 : 2.41 relevée sur le pilote). Le paquet `zsh-syntax-highlighting` reste optionnel dans le bootstrap commun et chargé en dernier par `.zshrc`.

Sur un serveur existant, ne pas relancer le bootstrap complet. Avant l'installation, vérifier que `~/.config` (ou `XDG_CONFIG_HOME`) et son sous-répertoire `atuin` ne sont pas des liens de répertoire vers le dépôt. Le pliage Stow peut avoir lié tout ce répertoire : l'installateur écrirait alors son reçu dans l'arborescence du dépôt. Après examen des conflits, simuler `stow --simulate --verbose --restow --no-folding --target "$HOME" shell`, puis appliquer le même restow sans `--simulate` et vérifier les répertoires réels avant l'installateur. Cette préparation n'active pas le module `linux-server` ni la synchronisation ; les conteneurs d'un serveur Atuin éventuel restent hors périmètre. Après installation, `git status --short` ne doit pas signaler de reçu ajouté au dépôt.

Sous le compte utilisateur, installer ensuite uniquement le client :

```bash
bash bootstrap/linux/install-atuin.sh
```

Le script nécessite curl, sha256sum et Python 3 (fourni par le profil serveur pour valider le reçu JSON). Il vérifie par SHA-256 l'installateur de la release officielle initiale 18.24.1 avant exécution ; celui-ci installe sous `~/.atuin/bin` et écrit son reçu dans `${XDG_CONFIG_HOME:-$HOME/.config}/atuin/atuin-receipt.json`. Aucun sudo, import, login ou sync n'est lancé ; le PATH et les fichiers shell ne sont pas modifiés par l'installateur. Le wrapper global `setup.atuin.sh` n'est pas utilisé car il peut aussi modifier les shells et installer des hooks d'agents. Un client autonome existant avec reçu JSON valide et correspondant à ce chemin est conservé s'il est au moins en 18.24.1 ; s'il est trop ancien, le script demande une mise à jour explicite, sans l'écraser. Les installations partielles ou non gérées et les reçus invalides sont refusés pour examen.

Avant de migrer des données existantes, fermer les autres sessions utilisateur qui invoquent Atuin, passer dans `exec zsh -f` pour suspendre les hooks et conserver le profil manuel. Relever les chemins avec l'ancien client `atuin info`, puis copier l'ensemble du répertoire de données et la configuration dans un répertoire privé hors dépôt, y compris clé, session et fichiers SQLite/WAL. Ne pas reprendre un ancien client sur une base migrée. Une copie du clone versionné n'est pas nécessaire ; préserver séparément les modifications locales utiles et les données non versionnées. Le retour en arrière exige une reprise cohérente de la copie des données et du client correspondant, pas seulement un changement de binaire ; il n'annule pas les échanges déjà effectués avec le serveur.

Tant que le PATH n'est pas validé, utiliser explicitement `~/.atuin/bin/atuin`. `.zshrc` donne priorité à ce chemin sur Linux avant l'initialisation ; les Mac conservent leur sélection Homebrew. Pour un pilote après migration, rester en mode manuel, contrôler la synchronisation et l'historique, puis seulement déployer le profil automatique. Un paquet APT préexistant n'est pas supprimé par le bootstrap : après validation du client récent et de sa priorité, examiner son retrait séparément avec une simulation APT, sans purge de données ni autoremove implicite.

Si un fichier ordinaire `~/.config/atuin/config.toml` bloque Stow, examiner ses réglages et le préserver hors dépôt ; ne pas utiliser `--adopt`. Les hooks du shell courant peuvent le recréer : déplacer ce fichier puis exécuter Stow dans un même Bash non interactif, après simulation et sans reprise des hooks entre les deux. Le dépliage de `.config/zsh` est normal quand `shell` et `linux-server` partagent ce répertoire.

Depuis le clone du serveur, après sauvegarde et examen des éventuels conflits, déployer le profil explicite avec le module partagé :

```bash
stow --simulate --verbose --target "$HOME" shell linux-server
stow --restow --target "$HOME" shell linux-server
```

Ouvrir une nouvelle session Zsh. Contrôler `command -v atuin` (attendu `~/.atuin/bin/atuin`) et `atuin --version`, jamais l'ancien client APT. Le fichier `~/.config/zsh/linux-server.zsh` sélectionne le profil automatique avant l'initialisation Atuin ; les fichiers Zsh locaux et par hôte chargés ensuite peuvent le remplacer. Les Mac ne reçoivent pas ce module. Vérifier `printenv ATUIN_CONFIG_DIR`, puis les valeurs résolues `sync_address`, `auto_sync` et `sync_frequency` (`https://atuin.hwapp.ovh`, `true`, `5m`) avec `atuin config get <cle> --resolved` si disponible.

Utiliser le compte existant : `atuin login -u <username>`, avec mot de passe et clé de chiffrement saisis aux invites, jamais en arguments ni dans le dépôt. Ne pas rouvrir les inscriptions et ne pas transmettre les sorties contenant la clé ou la session. L'import de l'ancien historique avec `atuin import zsh` est facultatif : le vérifier localement avant tout envoi, car il peut contenir des secrets. `atuin sync` échange l'historique chiffré avec le compte commun ; la synchronisation peut télécharger l'historique des autres machines sur ce serveur. Ne connecter que les comptes administrateur de confiance.

Contrôler une synchronisation manuelle puis le passage automatique après plus de cinq minutes d'activité, et `Ctrl+R`, la flèche haut et la coloration d'une commande sans l'exécuter. Aucun daemon, timer, changement SSH ou service serveur n'est nécessaire. En cas de régression, arrêter la diffusion ; dans la session courante, exporter d'abord `ATUIN_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/atuin"`, puis retirer seulement `linux-server` avec `stow --delete --target "$HOME" linux-server`. Fermer les autres sessions ayant conservé le profil automatique. Une nouvelle session utilise alors le mode manuel, sauf surcharge locale ; le repliage éventuel du répertoire Zsh ne supprime pas les alias du module `shell`. Ne pas supprimer les bases, la session ou la clé ; les historiques déjà synchronisés ne sont pas annulés par ce retour au mode manuel.

Après un échec de décodage sur un ancien client, un sync récent réussi peut ne traiter que les nouveaux records et laisser l'historique consultable incomplet. Dans le shell sans hooks, avec le profil manuel et le client récent par chemin absolu, examiner `atuin store status`, puis `atuin store verify`. Les index des séries ne sont pas des nombres exacts d'entrées consultables. Si le store contient les séries attendues et que le déchiffrement est vérifié, une réparation distincte approuvée peut exécuter `atuin store rebuild history` : reconstruction locale de la base dérivée, sans modification du serveur. Compter sans afficher l'historique avec `atuin history list --format 'entry' | wc -l`, en Bash avec `set -o pipefail`. Ne pas employer purge/rekey/force pour contourner une incompatibilité de version.

### Mises à jour du client Linux

Le canal autonome ne dépend pas des mises à jour APT et aucun timer n'est installé. Lors de la maintenance, vérifier le client utilisé puis les mises à jour proposées :

```bash
command -v atuin
atuin --version
atuin update --check
```

Après examen de la release et sauvegarde des données avant migration, mettre à jour sous le compte utilisateur avec `atuin update`, puis ouvrir une nouvelle session et refaire les contrôles de version, recherche et synchronisation. Le reçu de l'installateur est nécessaire : une simple copie du binaire n'offre pas ce mécanisme. La version initiale du bootstrap n'est pas un pinning/hold ; le script ne rétrograde pas une installation plus récente. `update_check = false` désactive les notifications automatiques du shell, pas les commandes explicites de contrôle/mise à jour. Ne pas activer le canal nightly ou une mise à jour automatique implicite.

Sources : [support Linux](https://docs.atuin.sh/latest/support/), [release officielle 18.24.1](https://github.com/atuinsh/atuin/releases/tag/v18.24.1), [implémentation de l'update autonome](https://github.com/atuinsh/atuin/blob/v18.24.1/crates/atuin/src/command/client/update.rs).

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
