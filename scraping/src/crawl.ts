import fs from "node:fs/promises";
import path from "node:path";
import { config } from "./config.js";
import { readCsv, writeCsv } from "./csv.js";
import { closeBrowser, fetchHttp, fetchWithPlaywright, isPlaywrightAvailable } from "./fetcher.js";
import { dedupePages, extractInternalLinks, extractText, extractTitle, visitKey } from "./pages.js";
import type { PageResult, SiteResult } from "./types.js";

const headers = [
  "domaine", "url", "titre", "statut_http", "methode", "contenu_texte", "date_collecte", "erreur"
];

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

interface DomainTarget {
  domaine: string;
  url: string;
}

interface DomainReport {
  domaine: string;
  pages: number;
  errors: string[];
}

// robots.txt et sitemap.xml désactivés à la demande : deux requêtes et deux
// pauses en moins par domaine. Le module src/robots.ts reste disponible.


// HTTP d'abord ; Playwright seulement si le HTML est vide ou trop pauvre.
async function fetchPage(url: string): Promise<ReturnType<typeof fetchHttp>> {
  const httpOutcome = await fetchHttp(url);
  const text = httpOutcome.html ? extractText(httpOutcome.html) : "";
  const needsBrowser = !httpOutcome.html || text.length < config.crawl.minTextLength;
  if (!needsBrowser || !isPlaywrightAvailable()) return httpOutcome;

  const browserOutcome = await fetchWithPlaywright(url);
  if (browserOutcome.html && extractText(browserOutcome.html).length > text.length) {
    return browserOutcome;
  }
  return httpOutcome;
}

async function crawlDomain(target: DomainTarget): Promise<{ pages: PageResult[]; report: DomainReport }> {
  const { domaine } = target;
  const pages: PageResult[] = [];
  const report: DomainReport = { domaine, pages: 0, errors: [] };

  let origin: string;
  try {
    origin = new URL(target.url).origin;
  } catch {
    report.errors.push("URL de départ invalide");
    return { pages, report };
  }

  const queue: string[] = [origin.endsWith("/") ? origin : `${origin}/`];
  const visited = new Set<string>();
  let linksCollected = false;

  while (queue.length > 0 && pages.length < config.crawl.maxPagesPerDomain) {
    const url = queue.shift() as string;
    if (visited.has(visitKey(url))) continue;
    visited.add(visitKey(url));

    const outcome = await fetchPage(url);
    const html = outcome.html;
    // Une redirection peut mener à une page déjà enregistrée.
    const finalKey = visitKey(outcome.finalUrl);
    if (finalKey !== visitKey(url) && visited.has(finalKey)) {
      console.log(`  ${url} — redirection vers une page déjà visitée`);
      await wait(config.crawl.delayMs);
      continue;
    }
    visited.add(finalKey);

    const record: PageResult = {
      domaine,
      url: outcome.finalUrl,
      titre: html ? extractTitle(html) : "",
      statut_http: outcome.status,
      methode: outcome.method,
      contenu_texte: html ? extractText(html) : "",
      date_collecte: new Date().toISOString(),
      erreur: outcome.error
    };
    pages.push(record);
    if (outcome.error) report.errors.push(`${url} — ${outcome.error}`);
    console.log(
      `  ${url} — ${outcome.status || "erreur"} | ${outcome.method || "aucune"} | ` +
      `${record.contenu_texte.length} car.${outcome.error ? ` | ${outcome.error}` : ""}`
    );

    // Les liens internes sont collectés une seule fois, sur la page d'accueil.
    if (!linksCollected && html) {
      linksCollected = true;
      const links = extractInternalLinks(html, outcome.finalUrl, domaine)
        .filter((link) => link.score > 0 && !visited.has(visitKey(link.url)))
        .slice(0, config.crawl.maxPagesPerDomain * 2);
      queue.push(...links.map((link) => link.url));
      console.log(`  ${links.length} lien(s) interne(s) prioritaire(s) retenu(s)`);
    }

    await wait(config.crawl.delayMs);
  }

  report.pages = pages.length;
  return { pages, report };
}

async function runWithConcurrency(
  targets: DomainTarget[],
  limit: number,
  worker: (target: DomainTarget) => Promise<void>
): Promise<void> {
  let cursor = 0;
  const runners = Array.from({ length: Math.max(1, Math.min(limit, targets.length)) }, async () => {
    while (cursor < targets.length) {
      const target = targets[cursor];
      cursor += 1;
      await worker(target);
    }
  });
  await Promise.all(runners);
}

async function main(): Promise<void> {
  const sites = await readCsv(config.sitesFile) as unknown as SiteResult[];
  const existing = await readCsv(config.pagesFile).catch((error) => {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw error;
  }) as unknown as PageResult[];

  const alreadyCrawled = new Set(existing.map((page) => page.domaine));
  const targets: DomainTarget[] = [];
  const seen = new Set<string>();
  for (const site of sites) {
    if (!site.domaine || seen.has(site.domaine) || alreadyCrawled.has(site.domaine)) continue;
    seen.add(site.domaine);
    targets.push({ domaine: site.domaine, url: site.url });
  }

  console.log(`Domaines dans sites.csv : ${seen.size + alreadyCrawled.size}`);
  console.log(`Déjà crawlés (ignorés) : ${alreadyCrawled.size}`);
  console.log(`À traiter : ${targets.length}`);
  const collected: PageResult[] = [...existing];
  const reports: DomainReport[] = [];

  if (targets.length > 0) {
    await runWithConcurrency(targets, config.crawl.concurrency, async (target) => {
      console.log(`\n[${target.domaine}]`);
      const { pages, report } = await crawlDomain(target);
      collected.push(...pages);
      reports.push(report);
    });
    await closeBrowser();
  }

  const { rows, duplicatesRemoved } = dedupePages(collected);
  rows.sort((a, b) => a.domaine.localeCompare(b.domaine) || a.url.localeCompare(b.url));
  await fs.mkdir(path.dirname(config.pagesFile), { recursive: true });
  await writeCsv(config.pagesFile, headers, rows as unknown as Record<string, unknown>[]);

  const domainsInFile = new Set(rows.map((page) => page.domaine));
  const failedRows = rows.filter((page) => page.erreur);
  console.log(`\n=== Résumé ===`);
  console.log(`Sites présents dans pages.csv : ${domainsInFile.size}`);
  console.log(`Sites crawlés lors de ce run : ${reports.length}`);
  console.log(`Pages enregistrées : ${rows.length}`);
  console.log(`Doublons supprimés : ${duplicatesRemoved}`);
  console.log(`Pages sans contenu exploitable : ${rows.filter((page) => !page.contenu_texte).length}`);

  if (failedRows.length === 0) {
    console.log("Sites en erreur : aucun");
  } else {
    const failedDomains = new Set(failedRows.map((page) => page.domaine));
    console.log(`\nSites en erreur : ${failedDomains.size}`);
    for (const page of failedRows) console.log(`  ${page.domaine} : ${page.url} — ${page.erreur}`);
  }
  console.log(`\nFichier : ${config.pagesFile}`);
}

main().catch(async (error) => {
  await closeBrowser();
  console.error(`Échec : ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
});
