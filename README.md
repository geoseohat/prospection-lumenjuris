# Prospection Lumen Juris

Chaîne quotidienne : recherche Google de professionnels du droit, extraction des
emails depuis leur site, envoi d'un message personnalisé, suivi dans Google Sheets.

## Commande unique

```bash
python routine.py
```

Elle lit sa configuration dans le Google Sheet, s'arrête si `ACTIF` n'est pas à
`oui`, complète le stock de leads, puis envoie les emails en respectant les quotas.

Autres commandes utiles :

| Commande | Effet |
|---|---|
| `python routine.py --etat` | état du stock, des quotas et des envois, sans rien envoyer |
| `python routine.py --simule --envoi` | affiche les messages sans les envoyer |
| `python routine.py --recolte` | constitue le stock seulement |
| `python routine.py --test-vers adresse@exemple.fr` | un seul message réel, personnalisé |

## Installation

```bash
pip install -r requirements.txt
cd scraping && npm install
```

## Secrets

Aucun secret n'est versionné. En local ils sont lus dans `mdp.txt`,
`scraping/.env` et `service-account.json`. En ligne, ils viennent des variables
d'environnement, qui sont prioritaires :

| Variable | Contenu |
|---|---|
| `SMTP_PASS_LUMEN` | mot de passe de `contact@lumenjuris.com` |
| `SMTP_PASS_GEOFFREY` | mot de passe d'application Gmail |
| `SERPAPI_API_KEY` | clé SerpApi |
| `SCRAPEDO_API_KEY` | clé Scrape.do, utilisée quand SerpApi est épuisé |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | contenu entier du compte de service, sur une ligne |

## Suivi

Tout est visible dans le Google Sheet, quatre onglets :

- **Routine** — état de la tâche planifiée, quotas, stock, réglages en cours
- **Config** — `ACTIF`, `MAX_PAR_BOITE`, `MAX_PAR_DOMAINE`, `PAUSE_MINUTES`, `STOCK_CIBLE`
- **Leads** — un lead par ligne, avec son état et l'expéditeur utilisé
- **Journal** — une ligne par email envoyé, plus un résumé par exécution

Pour arrêter la routine : mettre `ACTIF` sur `non` dans l'onglet `Config`.

## Garanties

- Une adresse n'est **jamais** contactée deux fois.
- Un site reçoit au plus `MAX_PAR_DOMAINE` messages, tous envois confondus.
- Si la base locale est absente, elle est reconstruite depuis le Sheet. Si le
  Sheet est illisible **et** la base vide, la routine s'arrête sans rien envoyer
  plutôt que de risquer de recontacter tout le monde.
- Quand SerpApi est épuisé, bascule automatique sur Scrape.do. Les deux épuisés,
  l'envoi continue avec le stock existant.

## Organisation

| Fichier | Rôle |
|---|---|
| `routine.py` | orchestrateur, seul point d'entrée |
| `base.py` | base SQLite, anti-doublon, journal |
| `sheets.py` | lecture et écriture du Google Sheet |
| `personnalisation.py` | objet et corps du message, à partir des données du site |
| `requetes.py` | 370 combinaisons ville × spécialité, jamais réutilisées |
| `envoi.py` | comptes SMTP, composition et envoi |
| `scraping/` | recherche Google, visite des sites, extraction des emails (TypeScript) |
