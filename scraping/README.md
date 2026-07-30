# Prospection avocats Lumen Juris — étape 1

Ce projet recherche des sites officiels de professionnels du droit à partir de `recherches.csv`. Il ne visite pas les pages internes, ne collecte pas d’emails et n’écrit ni dans Gmail ni dans Google Sheets.

## APIs vérifiées

- **SerpApi** : `GET https://serpapi.com/search`, paramètres utilisés `engine=google`, `q`, `api_key`, `output=json`, `google_domain=google.fr`, `gl=fr`, `hl=fr`. Les résultats naturels sont lus dans `organic_results`.
- **Scrape.do** : `GET https://api.scrape.do/plugin/google/search`, paramètres utilisés `token`, `q`, `device=desktop`, `start=0`. Les résultats naturels sont lus dans `organic_results`.

La documentation officielle Scrape.do consultée pour cette intégration décrit Google, pas Bing. Les deux fournisseurs utilisent donc Google pour cette première étape.

## Installation

```bash
npm install
```

Copier les variables de `.env.example` dans `.env`, puis renseigner les clés localement. Les clés ne doivent jamais être commitées ni affichées dans les logs.

```dotenv
SERPAPI_API_KEY=
SCRAPEDO_API_KEY=
SERPAPI_REQUEST_LIMIT=249
SCRAPEDO_REQUEST_LIMIT=1000
```

## Utilisation

```bash
npm run search
```

Le programme :

1. lit `recherches.csv` ;
2. réserve et persiste chaque requête dans `results/api-usage.json` avant l’appel réseau ;
3. choisit SerpApi jusqu’à sa limite mensuelle, puis Scrape.do ;
4. conserve uniquement les résultats naturels plausiblement officiels et pertinents ;
5. exclut réseaux sociaux, annuaires et plateformes ;
6. déduplique par domaine en conservant la meilleure position ;
7. écrit le résultat dans `sites.csv`.

### Re-filtrage sans appel API

```bash
npm run refilter
```

Réapplique les filtres courants (`config/excluded-domains.json` et `src/filters.ts`) au `sites.csv` déjà produit, puis réécrit le fichier. Utile après un durcissement du filtrage : aucune requête n’est consommée et les compteurs restent inchangés.

Les compteurs sont séparés par mois (`YYYY-MM`) et les limites viennent exclusivement de `.env`. Si aucune clé n’est configurée, ou si tous les fournisseurs disponibles ont atteint leur quota, le programme s’arrête avec une alerte sans consommer de requête.

## Étape 2 — visite des sites

```bash
npm run crawl
```

Lit les domaines de `sites.csv`, ignore ceux déjà présents dans `results/pages.csv` (reprise possible après interruption), visite la page d’accueil puis les liens internes les mieux classés, et écrit `results/pages.csv`.

- requête HTTP en priorité, Cheerio pour l’analyse ;
- Playwright uniquement si le HTML rendu est vide ou trop pauvre, et seulement s’il est installé (`npm i -D playwright && npx playwright install chromium`) ;
- même domaine uniquement, sous-domaines inclus ;
- 4 pages maximum par domaine, 2 domaines en parallèle, 1 s entre deux requêtes vers le même domaine, timeout 15 s ;
- aucun formulaire soumis, aucun blocage contourné ;
- déduplication des pages atteintes par deux URL (`/contact` et `/contact/`, avec ou sans `www`).

Réglages surchargeables dans `.env` : `CRAWL_MAX_PAGES`, `CRAWL_CONCURRENCY`, `CRAWL_TIMEOUT_MS`, `CRAWL_DELAY_MS`, `CRAWL_MIN_TEXT`.

La lecture de `robots.txt` et la détection de `sitemap.xml` ont été désactivées dans `crawl.ts` pour réduire le temps d’exécution. Le module `src/robots.ts` et ses tests restent en place pour les réactiver.

## Tests

```bash
npm test
npm run typecheck
```

Les tests couvrent le nettoyage des URL, l’exclusion des domaines, la déduplication et la détection des sites non pertinents (écoles, plateformes de freelances, portage salarial, contenus éditoriaux).
