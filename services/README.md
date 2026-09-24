# Bases locales DBngin et services OrbStack

Les opérations se font manuellement sur chaque Mac. MySQL et PostgreSQL sont
gérés dans DBngin ; OrbStack/Compose héberge Mailpit et, selon les projets,
Redis et Meilisearch. PHP et Node restent natifs sur macOS. Aucun démarrage
ou arrêt de Compose ne pilote les bases SQL.

## MySQL et PostgreSQL dans DBngin

1. Installer DBngin via `brew/Brewfile`, puis vérifier la disponibilité des
   versions correspondant aux instances sources déclarées : MySQL `8.0.33` et
   PostgreSQL `16.4`. Si une version n'est plus disponible, vérifier la
   compatibilité des exports avant de choisir une version cible ; ne pas
   changer de version majeure implicitement.
2. Créer les instances dans DBngin, relever leurs ports et régler leurs accès
   locaux. Prévoir les bases, utilisateurs, droits et extensions attendus par
   chaque projet. Ne pas mettre de mot de passe SQL dans ce dépôt ou dans
   `services/.env.example` ; ne pas réutiliser d'identifiants de production.
3. Restaurer les exports logiques des anciennes instances avec des clients
   compatibles avec les versions retenues. La copie brute d'un répertoire de
   données actif n'est pas un export. Vérifier schémas, données, routines et
   événements MySQL, extensions et rôles PostgreSQL, encodages et collations.
   Contrôler les connexions dans TablePlus et dans les applications.
4. Configurer les projets natifs vers `127.0.0.1` et les ports DBngin relevés.
   Certains clients MySQL utilisent un socket Unix pour `localhost` : choisir
   explicitement TCP si c'est le mode attendu. Vérifier l'écoute réseau et les
   conflits avec d'anciennes instances ou d'anciens conteneurs SQL.

Ne pas supprimer les anciens volumes Compose SQL ou les anciennes données DBngin
sur la seule base du retrait de leurs définitions dans ce dépôt. Garder une
copie et un export jusqu'à validation d'une restauration dans DBngin.

### Exports et restauration de contrôle

Utiliser l'outil d'export de DBngin ou les clients `mysqldump`/`pg_dump`
compatibles avec les serveurs réellement installés. Vérifier la version des
clients avant usage et adapter les noms de bases, comptes et ports. Pour MySQL,
`--single-transaction` suppose des tables transactionnelles ; suspendre les
écritures si ce n'est pas le cas. Sauvegarder aussi les utilisateurs/rôles
globaux nécessaires : les dumps d'une seule base ne les incluent pas.

Créer des exports cohérents dans un dossier du Mac inclus dans Time Machine,
avec des permissions restrictives et une rétention locale adaptée. Restaurer
un export dans une **nouvelle base/instance de test compatible**, jamais par
dessus la base de travail. Valider tables, données et droits avec les applications.
Vérifier la couverture réelle des données DBngin par Time Machine ; une copie
à chaud de ses fichiers ne remplace pas ces exports. Voir le runbook Fieldbook
`macos-installation.md` et `macos-timemachine.md` pour les sauvegardes des Mac.

## Préparer OrbStack et Compose

1. Installer/lancer OrbStack et vérifier `docker context show`, `docker version`
   et `docker compose version`.
2. Copier `services/.env.example` dans `~/.config/dev-services/local.env`, après
   création de son dossier, puis limiter ses permissions à `600`. Les valeurs
   Redis et Meilisearch ne sont requises que pour leurs fichiers Compose.
3. Depuis la racine du dépôt :

   ```bash
   export DEV_SERVICES_ENV="$HOME/.config/dev-services/local.env"
   docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml config --quiet
   docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml up -d --wait mailpit
   docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml ps
   ```

Mailpit écoute sur SMTP `127.0.0.1:1025` et sur
`http://127.0.0.1:8025` par défaut (ports configurables dans le fichier
local). Les messages de développement sont jetables, limités à 500 et sans
volume persistant. Pour Laravel, renseigner `MAIL_MAILER=smtp`,
`MAIL_HOST=127.0.0.1`, `MAIL_PORT=1025`, sans authentification ni TLS si le
projet le permet ; envoyer et retrouver un message de test dans l'interface.

Mailpit `1.31.2` est fixé par digest ARM64 dans `services/compose.yaml`. Les
profils empêchent son démarrage implicite et aucun redémarrage automatique
n'est configuré. Les ports Compose sont liés uniquement à `127.0.0.1`.

## Redis et Meilisearch à la demande

Choisir une image avec version explicite ou digest selon les projets, puis
vérifier sa disponibilité ARM64. Meilisearch exige une clé locale d'au moins
16 octets ; ne pas publier la sortie de `docker compose config` sans `--quiet`
si elle contient des secrets interpolés. Les variables déjà exportées dans le
shell ont priorité sur le fichier local.

```bash
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.redis.yaml config --quiet
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.redis.yaml up -d --wait

docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.meilisearch.yaml config --quiet
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.meilisearch.yaml up -d
curl --fail http://127.0.0.1:7700/health
```

Meilisearch n'a pas de healthcheck interne tant que les outils disponibles
dans l'image retenue ne sont pas vérifiés ; contrôler son endpoint et un index
depuis l'application. Redis conserve l'AOF dans son volume. Décider si ces
données sont reconstituables ; sinon ajouter leurs exports à la stratégie de
sauvegarde avant toute exclusion de la VM OrbStack dans Time Machine.

## Arrêt et entretien

```bash
docker compose --env-file "$DEV_SERVICES_ENV" -f services/compose.yaml stop mailpit
```

Utiliser de même `stop` avec le fichier Redis ou Meilisearch. Démarrer/arrêter
MySQL et PostgreSQL dans DBngin indépendamment. Ne pas utiliser `down -v` ni
un nettoyage global des volumes comme entretien courant. Mesurer mémoire et
swap sur Tatooine avec PhpStorm et les services réellement nécessaires.
