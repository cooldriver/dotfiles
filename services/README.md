# Services locaux sur OrbStack

Les commandes suivantes sont à exécuter manuellement depuis la racine de Dotfiles.
Elles ne déploient rien sur AWS. PHP et Node restent natifs sur macOS.

## Préparer les paramètres

1. Installer/lancer OrbStack et vérifier `docker context show`, `docker version`
   et `docker compose version`.
2. Copier `services/.env.example` dans `~/.config/dev-services/local.env`, après
   création de son dossier. Lui donner les permissions `600` et renseigner les
   mots de passe SQL locaux. Ne pas utiliser des credentials de production.
3. Tous les mots de passe SQL sont requis par l'interpolation Compose, même si
   un seul service SQL est démarré. Redis et Meilisearch sont dans des fichiers
   distincts pour que leurs versions encore inconnues ne bloquent pas ce socle.
4. Dans le terminal courant :

   ```bash
   export DEV_SERVICES_ENV="$HOME/.config/dev-services/local.env"
   docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml config --quiet
   ```

Ne pas publier la sortie de `config` sans `--quiet` : elle contient les secrets
interpolés. Les variables déjà exportées dans le shell ont priorité sur le fichier.

## Démarrer uniquement les services nécessaires

```bash
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml up -d --wait mysql mailpit
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml up -d --wait postgres
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml ps
```

Les profils empêchent un simple `up` de lancer tous les services. Un service
explicitement nommé est démarré sans avoir à activer son profil. Aucun service
n'est configuré pour redémarrer automatiquement avec le moteur.

- MySQL : `127.0.0.1:3306`, base/utilisateur `dev` par défaut.
- PostgreSQL : `127.0.0.1:5432`, base/utilisateur `dev` par défaut. Le compte
  d'initialisation est superutilisateur ; créer des rôles applicatifs séparés si
  les tests doivent reproduire des permissions plus fines.
- Mailpit : SMTP `127.0.0.1:1025`, interface `http://127.0.0.1:8025`.
  Messages de développement jetables, limités à 500, sans volume persistant.

Les ports sont liés uniquement à la boucle locale. Ils restent accessibles aux
processus locaux. Arrêter DBngin ou changer les ports avant le test si un serveur
natif les utilise déjà. Dans les applications natives, utiliser `127.0.0.1` plutôt
que les noms de services Compose. Pour Laravel, configurer `MAIL_MAILER=smtp`,
`MAIL_HOST=127.0.0.1`, `MAIL_PORT=1025`, sans authentification ni TLS, selon les
paramètres disponibles dans la version du projet.

## Versions et migration

Le socle reprend les versions sources MySQL 8.0.33 et PostgreSQL 16.4 pour isoler
la migration de toute montée de version. Mailpit 1.31.2 est retenu pour le pilote.
Les trois tags et leurs manifests ARM64 ont été vérifiés sur Docker Hub le
2026-09-21 ; leurs digests sont fixés dans Compose. Leur démarrage et les imports
applicatifs restent à tester sur Tatooine. Ces anciennes versions SQL constituent
une référence de migration ; planifier ensuite leur mise à jour séparément.

Les volumes nommés restent dans le stockage Linux d'OrbStack. Ne pas monter un
répertoire macOS pour les fichiers de données SQL. Les mots de passe et noms de
bases d'initialisation ne s'appliquent qu'à un volume vide : changer `local.env`
ne change pas les utilisateurs existants.

## Export et restauration de contrôle

Créer un dossier de sauvegarde hors Dotfiles, inclus dans Time Machine. Exemples
pour la base `dev` ; adapter les noms aux vraies bases sans les écraser. Les exports
suivants couvrent les bases applicatives, pas les utilisateurs/rôles SQL globaux.
Relever séparément ces derniers si nécessaires. Pour MySQL, `--single-transaction`
suppose des tables transactionnelles ; suspendre les écritures pour les autres.

```bash
umask 077
mkdir -p "$HOME/Backups/dev-services"

docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump -uroot --single-transaction --routines --events --triggers --set-gtid-purged=OFF "$MYSQL_DATABASE"' \
  > "$HOME/Backups/dev-services/mysql.sql.partial" &&
  mv "$HOME/Backups/dev-services/mysql.sql.partial" "$HOME/Backups/dev-services/mysql.sql"

docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml exec -T postgres \
  sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
  > "$HOME/Backups/dev-services/postgres.dump.partial" &&
  mv "$HOME/Backups/dev-services/postgres.dump.partial" "$HOME/Backups/dev-services/postgres.dump"
```

Restaurer dans des bases de test **neuves**, sans supprimer les bases de travail :

```bash
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot -e "CREATE DATABASE restore_check"' &&
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml exec -T mysql \
  sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot restore_check' \
  < "$HOME/Backups/dev-services/mysql.sql"

docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml exec -T postgres \
  sh -c 'exec createdb -U "$POSTGRES_USER" restore_check' &&
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml exec -T postgres \
  sh -c 'exec pg_restore --exit-on-error -U "$POSTGRES_USER" -d restore_check' \
  < "$HOME/Backups/dev-services/postgres.dump"
```

La création échoue si `restore_check` existe déjà : choisir un autre nom pour un
nouvel essai. Contrôler tables, données et accès depuis TablePlus. Pour le premier
import DBngin, utiliser ses exports logiques, relever les extensions PostgreSQL
et vérifier encodages/collations et routines avant validation.

## Redis et Meilisearch à la demande

Renseigner une image avec un tag explicite ou un digest dans le fichier local,
après relevé de la version nécessaire et vérification de son support ARM64.
Meilisearch exige aussi une clé locale d'au moins 16 octets.

```bash
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.redis.yaml config --quiet
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.redis.yaml up -d --wait

docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.meilisearch.yaml config --quiet
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.meilisearch.yaml up -d
curl --fail http://127.0.0.1:7700/health
```

Meilisearch n'a pas de healthcheck interne tant que les outils disponibles dans
l'image retenue ne sont pas vérifiés ; contrôler son endpoint et un index depuis
l'application. Redis conserve l'AOF dans son volume. Décider si ces données sont
reconstructibles ; sinon ajouter leurs exports à la stratégie de sauvegarde.

## Arrêt et entretien

```bash
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml stop mysql postgres mailpit
```

Utiliser de même `stop` avec le fichier Redis ou Meilisearch. Ne pas utiliser
`down -v` ni un nettoyage global des volumes comme entretien courant. Garder les
noms de projet Compose stables pour retrouver les volumes. Mesurer mémoire/swap
sur Tatooine avec PhpStorm et un vrai projet ; DBngin reste le repli possible si
les performances SQL ne conviennent pas.
