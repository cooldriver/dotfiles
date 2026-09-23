# Installation manuelle du socle macOS

Ce guide complète le runbook Fieldbook : effacement, installation de macOS et
configuration des NAS restent décrits dans le vault. Ici, les commandes sont
exécutées depuis la racine du dépôt Dotfiles après lecture de chaque étape.

## 1. Préparer Homebrew et les paquets

1. Installer les Command Line Tools et Homebrew depuis leurs sources officielles.
   Vérifier `uname -m` (`arm64`) et `brew --prefix` (`/opt/homebrew`).
2. Récupérer **la version préparée de ce dépôt** sur le nouveau Mac. Les fichiers
   modifiés localement ne sont pas disponibles sur GitHub tant qu'ils n'ont pas
   été publiés par le propriétaire. Préserver les permissions exécutables lors
   d'un transfert local.
3. Lire `brew/Brewfile`. Les anciennes formules PHP non versionnées, Ansible
   global, Redis/Meilisearch natifs et Proton Pass sont remplacés dans le parcours
   nominal. DBngin reste un repli à installer manuellement si le test SQL échoue.
4. Installer d'abord les outils nécessaires au déploiement et aux validations :

   ```bash
   brew install git stow direnv uv gh
   ```

5. Se connecter à l'App Store, puis appliquer le Brewfile revu :

   ```bash
   brew bundle install --file brew/Brewfile
   ```

6. Pour une progression plus fine, installer manuellement les formules/casks
   souhaités depuis la liste avant de relancer Bundle, qui complétera les entrées
   manquantes. `brew bundle list --file brew/Brewfile --formula` et `--cask`
   servent à afficher les catégories ; ces filtres ne sont pas des options de
   `brew bundle install`.

Ne pas utiliser `brew bundle cleanup` pour préparer un nouveau poste. L'option `require_sha` est
conservée : si un cask ne publie pas de somme de contrôle, examiner ce cas séparément.
1Password est explicitement installé dans `/Applications` pour stabiliser le chemin
de son programme de signature ; les autres casks utilisent `~/Applications`.

## 2. Shell et déploiement Stow

Installer Oh My Zsh et Spaceship selon le README, puis prévisualiser :

```bash
stow --simulate --verbose --target "$HOME" shell git vim btop zellij macos
```

Le paquet `macos` comprend maintenant `~/.config/direnv/direnvrc` et le lanceur
Composer. Le paquet `shell` fournit `with-github`, `gh-personal` et `gh-work`.
Si un fichier existe déjà, le sauvegarder et comparer avant de remplacer son
contenu ; en particulier, conserver les autres helpers direnv utiles.

Après résolution des conflits :

```bash
stow --target "$HOME" shell git vim btop zellij macos
```

Ouvrir un nouveau terminal de connexion : `~/.local/bin` doit être dans le PATH
et PHP 8.5 est la version par défaut. Les formules PHP sont installées sans
liaison globale ; aucun switch de liens n'est nécessaire.

Atuin est initialisé automatiquement par `.zshrc` lorsqu'il est installé :
la flèche haut ouvre sa recherche d'historique. La synchronisation privée est
automatique sur Tatooine et manuelle sur Toola ; voir
[Atuin](atuin.md) pour le déploiement et l'import initial. Les réglages visuels
iTerm2 et les préférences TUI restent des choix à ajuster pendant le pilote.
Zellij remplace tmux et utilise son mode normal par défaut : `Ctrl+R` et
`Ctrl+T` y contrôlent Zellij, tandis que la flèche haut reste à Atuin.
Voir [Zellij](zellij.md) pour les sessions locales et SSH.

## 3. PHP et Composer

Installer le PHAR de Composer vérifié, hors du dépôt :

```bash
bash bootstrap/macos/install-composer.sh
```

Le script fixe Composer 2.10.3 et vérifie le SHA-256 publié par Composer avant de
remplacer le PHAR. Sa distribution stable annonce PHP 7.2 ou supérieur. Le lanceur
`composer` déployé par Stow utilise le `php` du PATH : celui du projet quand
direnv est actif. Le PHAR est partagé, pas l'interpréteur.

Les `.envrc` existants restent compatibles :

```bash
strict_env
use php php@7.4
layout php
```

ou :

```bash
strict_env
use php php@8.5
layout php
```

`strict_env` rend une erreur de sélection bloquante lors de l'évaluation du
`.envrc`, même si d'autres directives suivent le helper. Dans un terminal
interactif, une erreur direnv n'empêche pas de taper une autre commande : la
résoudre et vérifier `php -v` avant de continuer avec le projet.

Après lecture, exécuter `direnv allow` dans chaque projet. Ouvrir les deux projets
dans deux terminaux, puis vérifier dans chacun :

```bash
command -v php
php -r 'echo PHP_VERSION, " ", PHP_BINARY, PHP_EOL;'
php --ini
command -v composer
composer --version
composer check-platform-reqs
```

Le terminal 7.4 doit rester en 7.4 après l'entrée dans le projet 8.5 de l'autre
terminal. `layout php` ajoute `vendor/bin` ; il ne choisit pas la version PHP.
Les alias ou fonctions personnels nommés `php`/`composer` doivent être examinés
s'ils masquent les exécutables sélectionnés.

Configurer l'interpréteur CLI **par projet** dans PhpStorm avec le chemin
`/opt/homebrew/opt/php@VERSION/bin/php`, ainsi que Composer et les tests. Les GUI
ne chargent pas automatiquement direnv. Pour un processus non interactif :

```bash
direnv exec /chemin/du/projet composer --version
```

Reprendre `composer dev`/`artisan serve`. Attribuer des ports distincts à chaque
projet simultané, y compris les serveurs front. Pour les rares sites Caddy,
prévoir un PHP-FPM de version et de port/socket explicites, indépendamment du
terminal actif.

## 4. Xdebug pour PHP 8.5 seulement

La formule `shivammathur/extensions/xdebug@8.5` fournit le binaire et sa directive
de chargement. Vérifier :

```bash
/opt/homebrew/opt/php@8.5/bin/php --ini
/opt/homebrew/opt/php@8.5/bin/php --ri xdebug
```

Lire `docs/php85-xdebug.ini`, puis le copier dans
`/opt/homebrew/etc/php/8.5/conf.d/99-local-xdebug.ini` si ce chemin correspond
aux fichiers effectivement chargés. Comparer avant remplacement s'il existe.
Ne pas dupliquer `zend_extension`. Aucun Xdebug n'est prévu dans PHP 7.4.

Dans PhpStorm, écouter sur le port 9003. Depuis un projet PHP 8.5, activer le
débogage à la demande :

```bash
XDEBUG_MODE=debug XDEBUG_TRIGGER=1 php artisan about
XDEBUG_MODE=debug php artisan serve --port=8000
```

Pour le navigateur, ajouter le déclencheur `XDEBUG_TRIGGER=1` à la requête ou
utiliser une extension de déclenchement. Placer un point d'arrêt réellement
traversé par la commande/requête testée. Le serveur doit avoir été démarré avec
le mode debug ; la couverture de tests utilise le mode `coverage` séparément.

## 5. GitHub personnel/professionnel et 1Password

1. Connecter 1Password, activer son agent SSH, puis exporter les clés **publiques**
   pro/perso. Les clés privées restent dans les coffres.
2. Adapter `docs/ssh-github-config.example` dans `~/.ssh/config`. Vérifier le chemin
   du socket avec les réglages de l'application installée.
3. Préparer `~/.config/git/personal.gitconfig` et `work.gitconfig` à partir de
   `docs/git-identities.example.gitconfig`. Renseigner les vrais noms/emails et les
   clés publiques de signature localement. Créer `~/.ssh/allowed_signers` avec une
   ligne `<email> <clé publique SSH>` par profil. Enregistrer les clés
   d'authentification et de signature sur les comptes GitHub correspondants.
4. Placer les dépôts dans `~/Developer/personal/` ou `~/Developer/work/`, et utiliser
   les alias SSH correspondants dans les remotes. Les anciens chemins
   `~/Repositories/` ne sont pas couverts automatiquement par `includeIf`.
5. Connecter chaque compte avec :

   ```bash
   gh auth login --hostname github.com --git-protocol ssh --web
   gh auth status
   ```

   Choisir le bon compte dans le navigateur et réutiliser les clés enregistrées.
6. Créer `~/.config/github/personal-user` et `~/.config/github/work-user` : chacun
   contient **uniquement le login GitHub**, sur une ligne, pas un jeton.
7. Tester depuis deux terminaux :

   ```bash
   gh-personal api user --jq .login
   gh-work api user --jq .login
   ssh -T git@github-personal
   ssh -T git@github-work
   git config --show-origin --get user.email
   git config --show-origin --get user.signingkey
   ```

`with-github` efface les tokens hérités avant de récupérer le token du login
explicitement choisi, puis le transmet uniquement au processus lancé. Il ne fait
pas de `gh auth switch`. Ne pas lancer ce script en traçage `bash -x`.

Pour un agent CLI dédié à une identité :

```bash
with-github LOGIN_WORK opencode
```

Pour les agents d'une application GUI ou d'un serveur partagé comme OpenChamber,
utiliser explicitement `gh-work`/`gh-personal` ou `with-github LOGIN gh ...` et
vérifier l'identité depuis le contexte réel. La connexion au modèle IA est
indépendante du compte GitHub. L'environnement d'une fenêtre existante n'est pas
modifié par un nouveau lancement depuis le terminal.

## 6. Services, infrastructure et sauvegarde

- Suivre [services/README.md](../services/README.md) pour SQL, Mailpit et les
  services optionnels. Relever Redis/Meilisearch avant de remplir leurs images.
- Installer les versions Node/Yarn déclarées par les projets. Ne pas régénérer
  leurs fichiers de verrouillage pendant la réinstallation.
- Le projet d'infrastructure gère Python/Ansible avec uv ; reproduire les versions
  et collections existantes avant toute évolution. Les fichiers du projet
  professionnel ne sont pas copiés dans ce dépôt public.
- AWS : utiliser des profils explicites, vérifier SSO puis AssumeRole et les
  consommateurs Terraform/Ansible. Aucun credential AWS global dans le shell.
- Time Machine : copier `docs/timemachine-exclusions.example.txt` dans un fichier
  local, revoir les chemins puis vérifier :

  ```bash
  bash bootstrap/macos/timemachine.sh --check "$HOME/.config/timemachine/exclusions.txt"
  ```

  Appliquer uniquement la liste revue avec `--apply`. Les chemins fixes continuent
  à exclure les dossiers recréés. Les dossiers absents peuvent être enregistrés
  lors de l'application ; le mode `--check` ne crée aucune exclusion. Après
  application, contrôler aussi les fichiers à conserver avec `tmutil isexcluded`.

## Vérification du dépôt sans déploiement

```bash
python3 -m unittest discover -s tests -v
shellcheck bootstrap/macos/*.sh macos/.config/direnv/direnvrc macos/.local/bin/composer shell/.local/bin/*
ruby -c brew/Brewfile
```

Les tests utilisent des homes temporaires, des commandes simulées et la validation
Compose sans démarrer de conteneur. Installer `direnv`, Stow et Docker Compose
pour exécuter aussi leurs tests d'intégration locale. La validation réelle de
Golden Gate, des services et des restaurations reste la recette de Tatooine.
