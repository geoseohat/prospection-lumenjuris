import fs from "node:fs/promises";
import { config } from "./config.js";
import { readCsv, writeCsv } from "./csv.js";
import { dedupeByDomain, isExcludedDomain, looksLikeOfficialRelevantSite } from "./filters.js";
import type { SiteResult } from "./types.js";

const headers = [
  "type_cible", "requete", "titre", "url", "domaine", "description",
  "position", "moteur", "source_api", "date_collecte"
];

// Réapplique les filtres au sites.csv existant, sans consommer d'appel API.
async function main(): Promise<void> {
  const rows = await readCsv(config.sitesFile) as unknown as SiteResult[];
  const excludedDomains = JSON.parse(await fs.readFile(config.excludedDomainsFile, "utf8")) as string[];

  const kept: SiteResult[] = [];
  const removed: SiteResult[] = [];
  for (const row of rows) {
    const site = { ...row, position: Number(row.position) };
    if (
      isExcludedDomain(site.domaine, excludedDomains) ||
      !looksLikeOfficialRelevantSite(site.titre, site.description, site.url, site.domaine)
    ) {
      removed.push(site);
      continue;
    }
    kept.push(site);
  }

  const { rows: deduped, duplicatesRemoved } = dedupeByDomain(kept);
  deduped.sort((a, b) => a.position - b.position || a.domaine.localeCompare(b.domaine));
  await writeCsv(config.sitesFile, headers, deduped as unknown as Record<string, unknown>[]);

  console.log(`Lignes lues : ${rows.length}`);
  for (const site of removed) console.log(`Retiré : ${site.domaine} — ${site.titre}`);
  console.log(`Lignes retirées : ${removed.length}`);
  console.log(`Doublons supprimés : ${duplicatesRemoved}`);
  console.log(`Domaines uniques conservés : ${deduped.length}`);
  console.log(`Fichier : ${config.sitesFile}`);
}

main().catch((error) => {
  console.error(`Échec : ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
});
