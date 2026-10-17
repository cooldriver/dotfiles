# Configuration SSH personnelle chiffrée

Ce workflow est réservé aux postes macOS. `age` est un programme de chiffrement, distinct de SSH et de 1Password. Il n'est pas nécessaire pour établir une connexion SSH après restauration. Le paquet Stow `ssh` est optionnel ; ne pas le déployer sur les serveurs Linux.

## Répartition

- `ssh/.ssh/config` est public et déployé par Stow vers `~/.ssh/config`. Il préserve l'inclusion OrbStack en tête, inclut les règles personnelles avant les réglages généraux, définit les alias `personalgit` et `workgit`, puis sélectionne l'agent 1Password et `IdentitiesOnly yes`. Les chemins de clés de ces alias sont définis dans le fichier privé afin de conserver les noms locaux sans les publier.
- `~/.ssh/config.private` est un fichier local, hors du dépôt, avec permissions `600`. Il contient les alias, IP, utilisateurs, chemins de clés publiques et éventuelles exceptions. Ne jamais y mettre de clé privée.
- `private/ssh/config.private.age` est sa version chiffrée versionnable ; `private/ssh/recipients.txt` contient uniquement le destinataire public `age`. Ce dossier n'est pas déployé par Stow.
- Les fichiers `~/.ssh/*.pub` sont exportés depuis 1Password. Les clés privées SSH restent dans son agent. Un fichier public sélectionne l'identité ; l'agent signe avec la clé privée correspondante.
- L'identité privée `age` est sauvegardée dans 1Password, jamais dans le dépôt. Prévoir également un moyen de récupération indépendant selon sa politique de sauvegarde : ne pas dépendre de la machine à restaurer pour retrouver cette identité.

## Initialisation unique : après validation de la migration

Ne pas exécuter cette section pendant la préparation. Sauvegarder la configuration SSH existante hors du dépôt. Construire et valider `~/.ssh/config.private` avant tout déploiement ; ne pas recopier aveuglément l'ancien fichier entier, notamment ses inclusions et blocs généraux.

Créer une identité native `age` avec `age-keygen -o <chemin-prive-hors-du-depot>`, dans un répertoire privé. Importer le fichier dans un élément **Document** de 1Password, pas dans un élément **Clé SSH** : une identité native `age` n'est pas une clé SSH et ne doit pas être ajoutée à son agent. Vérifier sa récupération et en déduire le destinataire public avec `age-keygen -y <chemin-prive-hors-du-depot>`. Enregistrer uniquement cette ligne publique `age1...` dans `private/ssh/recipients.txt`. Retirer la copie privée temporaire après vérification ; sa suppression ne garantit pas l'effacement physique sur SSD ou dans les sauvegardes. Ne jamais mettre l'identité dans un argument de commande, le presse-papiers partagé, les logs ou le dépôt.

Créer la première archive :

```bash
python3 -B scripts/ssh-private.py encrypt
```

Le script refuse une destination existante sans `--replace`, les fichiers de configuration ou archive symboliques et tout chemin de configuration en clair situé dans le dépôt. Tester une restauration vers un chemin temporaire privé hors du dépôt et comparer localement avec l'original avant de considérer la sauvegarde utilisable. Aucun outil n'inspecte automatiquement les secrets ou ne valide les règles SSH à votre place.

## Restaurer un nouveau Mac

1. Récupérer les dotfiles en HTTPS si nécessaire. Installer Python 3, Stow, `age` et 1Password ; connecter 1Password et activer son agent SSH. Le CLI `op` est nécessaire uniquement pour la restauration sans fichier d'identité local décrite ci-dessous. Configurer son [intégration avec l'application, les autorisations macOS et le test `op vault list`](macos-installation.md#intégration-du-cli-1password) avant de poursuivre.
2. Depuis la racine du dépôt, déchiffrer la configuration avec l'identité récupérée depuis le **Document** 1Password. Remplacer `DOCUMENT_ID` et `COFFRE` par les identifiants du document et de son coffre ; ne pas saisir la valeur secrète dans la commande. Dans Bash/Zsh, activer `pipefail` pour détecter aussi un échec de `op` :

   ```bash
   set -o pipefail
   op document get DOCUMENT_ID --vault COFFRE | python3 -B scripts/ssh-private.py decrypt --identity -
   ```

   L'identité passe par un pipe et n'est pas enregistrée par le script. Alternative : `--identity <fichier-prive-hors-du-depot>`. La restauration refuse toujours d'écraser un fichier existant, même avec `--replace`. Une erreur de déchiffrement ne publie aucun fichier de configuration partiel. Un arrêt brutal peut laisser un fichier temporaire `.ssh-private-*` privé dans le dossier cible ; l'inspecter localement et le retirer si nécessaire.
3. Lire `~/.ssh/config.private`, puis exporter depuis 1Password chaque clé publique référencée vers son chemin `IdentityFile`, y compris celles des alias GitHub `personalgit` et `workgit`. Conserver dans les commentaires privés la correspondance entre l'élément 1Password et le fichier attendu. Ne pas exporter les clés privées SSH ; aucune recopie manuelle des blocs GitHub n'est nécessaire.
4. Vérifier les fichiers préexistants sous `~/.ssh/`. S'il existe déjà un `config`, le sauvegarder et le déplacer explicitement hors du chemin de déploiement après comparaison. Ne pas utiliser `stow --adopt` ou forcer un écrasement. Le dossier `~/.ssh` doit rester local, pas devenir un lien vers le dépôt :

   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   stow --simulate --verbose --no-folding --target "$HOME" ssh
   stow --verbose --no-folding --target "$HOME" ssh
   ```

5. Vérifier avec `ssh -G <destination>` que `identityfile`, `identityagent` et `identitiesonly` correspondent aux attentes, puis tester des connexions représentatives. `ssh -G` ne contacte pas le serveur, mais une configuration contenant `Match exec` peut exécuter des commandes locales ; relire ces règles avant validation. Vérifier également OrbStack si utilisé. Les chemins `Include` basés sur `~` désignent le vrai HOME du processus, même avec `ssh -F` : ne pas employer ce dernier comme isolation de test.

## Modifier et persister

1. Modifier localement `~/.ssh/config.private` ; le socle public se modifie séparément dans `ssh/.ssh/config`.
2. Vérifier les paramètres effectifs et les connexions concernées. Les blocs spécifiques doivent précéder les blocs généraux ; SSH conserve généralement la première valeur rencontrée, tandis que plusieurs `IdentityFile` s'accumulent.
3. Chiffrer explicitement la nouvelle version :

   ```bash
   python3 -B scripts/ssh-private.py encrypt --replace
   ```

   Le destinataire public suffit : aucun accès à la clé privée `age` ou à 1Password n'est nécessaire. Le script ne remplace l'archive qu'après succès du chiffrement, via un fichier temporaire dans le même dossier. Il ne relit pas l'archive pour prouver sa restaurabilité ; vérifier le destinataire et refaire périodiquement un test de restauration.
4. Examiner les changements locaux. Le diff Git de l'archive n'est pas lisible ; la revue du contenu se fait avant chiffrement. Hervé réalise les commits et la publication. Une modification locale n'est pas sauvegardée tant que l'archive n'a pas été actualisée et publiée.

La publication révèle l'existence, la taille approximative et l'historique des mises à jour du fichier chiffré. Un changement de destinataire doit être accompagné d'une sauvegarde de sa nouvelle identité privée ; les anciennes révisions exigent toujours leurs anciennes identités pour être déchiffrées.
