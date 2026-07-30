import fs from "node:fs/promises";
import { config } from "./config.js";
import { readCsv, writeCsv } from "./csv.js";
import { dedupeByDomain, isExcludedDomain, looksLikeOfficialRelevantSite, normalizeUrl } from "./filters.js";
import { searchProvider } from "./providers.js";
import { currentUsage, loadUsage, reserveRequest, selectProvider } from "./usage.js";
import type { ProviderName, SearchInput, SiteResult } from "./types.js";

const headers = [
  "type_cible", "requete", "titre", "url", "domaine", "description",
  "position", "moteur", "source_api", "date_collecte"
];

async function main(): Promise<void> {
  const searches = await readCsv(config.searchesFile) as unknown as SearchInput[];
  const excludedDomains = JSON.parse(await fs.readFile(config.excludedDomainsFile, "utf8")) as string[];
  const usageFile = await loadUsage(config.usageFile);
  const limits = { serpapi: config.serpApiLimit, scrapedo: config.scrapeDoLimit };
  const keys: Record<ProviderName, string> = {
    serpapi: config.serpApiKey,
    scrapedo: config.scrapeDoApiKey
  };
  const availableKeys = { serpapi: Boolean(keys.serpapi), scrapedo: Boolean(keys.scrapedo) };

  if (!availableKeys.serpapi && !availableKeys.scrapedo) {
    throw new Error("Aucune clé API configurée. Renseignez SERPAPI_API_KEY ou SCRAPEDO_API_KEY dans .env.");
  }

  const collected: SiteResult[] = [];
  let totalExcluded = 0;
  let completedSearches = 0;

  for (const search of searches) {
    const usage = currentUsage(usageFile);
    const provider = selectProvider(usage, limits, availableKeys);
    if (!provider) {
      console.error("ALERTE : les deux quotas configurés sont atteints, ou aucune clé disponible ne permet de continuer.");
      break;
    }

    console.log(`\nRecherche : ${search.requete}`);
    console.log(`Fournisseur : ${provider} | moteur : Google`);
    await reserveRequest(config.usageFile, usageFile, provider, limits[provider]);

    try {
      const organic = await searchProvider(provider, search.requete, keys[provider]);
      console.log(`Résultats naturels reçus : ${organic.length}`);
      let kept = 0;
      let excluded = 0;
      for (const result of organic) {
        const normalized = normalizeUrl(result.link);
        if (
          !normalized ||
          isExcludedDomain(normalized.domain, excludedDomains) ||
          !looksLikeOfficialRelevantSite(result.title, result.snippet ?? "", normalized.url, normalized.domain)
        ) {
          excluded += 1;
          continue;
        }
        kept += 1;
        collected.push({
          type_cible: search.type_cible,
          requete: search.requete,
          titre: result.title.trim(),
          url: normalized.url,
          domaine: normalized.domain,
          description: (result.snippet ?? "").trim(),
          position: result.position,
          moteur: "google",
          source_api: provider,
          date_collecte: new Date().toISOString()
        });
      }
      totalExcluded += excluded;
      completedSearches += 1;
      console.log(`Sites conservés : ${kept}`);
      console.log(`Résultats exclus : ${excluded}`);
    } catch (error) {
      console.error(`Erreur : ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  const { rows, duplicatesRemoved } = dedupeByDomain(collected);
  rows.sort((a, b) => a.position - b.position || a.domaine.localeCompare(b.domaine));
  await writeCsv(config.sitesFile, headers, rows as unknown as Record<string, unknown>[]);
  const usage = currentUsage(usageFile);
  console.log(`\nDoublons supprimés : ${duplicatesRemoved}`);
  console.log(`Consommation SerpApi : ${usage.serpapi}/${limits.serpapi}`);
  console.log(`Consommation Scrape.do : ${usage.scrapedo}/${limits.scrapedo}`);
  console.log(`Nombre total de domaines uniques : ${rows.length}`);
  console.log(`Recherches réalisées : ${completedSearches}/${searches.length}`);
  console.log(`Résultats exclus au total : ${totalExcluded}`);
  console.log(`Fichier : ${config.sitesFile}`);
}

main().catch((error) => {
  console.error(`Échec : ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
});
