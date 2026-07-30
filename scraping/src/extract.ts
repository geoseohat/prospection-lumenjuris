import fs from "node:fs/promises";
import path from "node:path";
import { config } from "./config.js";
import { readCsv, writeCsv } from "./csv.js";
import {
  classifyEmail, emailMatchesSite, extractFromHtml, findEmailsInText, findLawyerNames,
  findPhone, findSpecialities, guessProfessionalType, looksLikeProfilePage, namesFromEmail,
  scoreConfidence
} from "./extraction.js";
import type { EmailHit } from "./extraction.js";
import { fetchHttp } from "./fetcher.js";
import type { PageResult, SiteResult } from "./types.js";

const headers = [
  "id", "type_cible", "cabinet", "prenom", "nom", "fonction", "specialites", "email",
  "type_email", "telephone", "site", "profil_url", "source_email_url", "personnalisation",
  "source_personnalisation_url", "niveau_confiance", "date_collecte"
];

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

interface Row {
  id: string;
  type_cible: string;
  cabinet: string;
  prenom: string;
  nom: string;
  fonction: string;
  specialites: string;
  email: string;
  type_email: string;
  telephone: string;
  site: string;
  profil_url: string;
  source_email_url: string;
  personnalisation: string;
  source_personnalisation_url: string;
  niveau_confiance: string;
  date_collecte: string;
}

function cabinetName(domain: string, pages: PageResult[]): string {
  const homepage = pages.find((page) => {
    try {
      return new URL(page.url).pathname.replace(/\/+$/, "") === "";
    } catch {
      return false;
    }
  });
  const title = (homepage ?? pages[0])?.titre ?? "";
  // Le premier segment du titre porte presque toujours le nom de la structure.
  const candidate = title.split(/[|–—]|\s-\s/)[0].trim();
  if (candidate.length >= 3 && candidate.length <= 70) return candidate;
  return domain
    .replace(/^www\./, "")
    .split(".")[0]
    .split(/[-_]/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

const functionPattern =
  /\b(avocat[e]?s?\s+(?:associ[ée]e?s?|collaborat(?:eur|rice)s?|fondat(?:eur|rice)s?|au\s+barreau[^.,;]{0,40})|avocat[e]?s?|juriste[s]?|consultant[e]?s?\s+juridique|of\s+counsel|associ[ée]e?\s+g[ée]rant[e]?|fondat(?:eur|rice))\b/i;

function findFunction(context: string): string {
  const match = functionPattern.exec(context);
  return match ? match[0].replace(/\s+/g, " ").trim() : "";
}

// La personnalisation doit être une phrase réellement écrite sur le site.
function buildPersonalisation(pages: PageResult[]): { texte: string; url: string } {
  for (const page of pages) {
    const sentences = page.contenu_texte.split(/(?<=[.!?])\s+/);
    for (const sentence of sentences) {
      const clean = sentence.replace(/\s+/g, " ").trim();
      if (clean.length < 60 || clean.length > 240) continue;
      if (!/droit\s+des\s+contrats|contractuel|droit\s+commercial|droit\s+des\s+affaires|contrats?\s+informatiques?|n[ée]gociation|r[ée]daction/i.test(clean)) {
        continue;
      }
      if (/cookie|consentement|navigateur|javascript|©/i.test(clean)) continue;
      return { texte: clean, url: page.url };
    }
  }
  const fallback = pages.find((page) => page.titre);
  return fallback ? { texte: fallback.titre.trim(), url: fallback.url } : { texte: "", url: "" };
}

async function refetchHtml(pages: PageResult[]): Promise<Array<{ url: string; html: string }>> {
  const results: Array<{ url: string; html: string }> = [];
  for (const page of pages) {
    const outcome = await fetchHttp(page.url);
    if (outcome.html) results.push({ url: outcome.finalUrl, html: outcome.html });
    await wait(config.crawl.delayMs);
  }
  return results;
}

async function main(): Promise<void> {
  const pages = await readCsv(config.pagesFile) as unknown as PageResult[];
  const sites = await readCsv(config.sitesFile) as unknown as SiteResult[];
  const siteUrlByDomain = new Map(sites.map((site) => [site.domaine, site.url]));

  const byDomain = new Map<string, PageResult[]>();
  for (const page of pages) {
    if (!page.domaine) continue;
    byDomain.set(page.domaine, [...(byDomain.get(page.domaine) ?? []), page]);
  }

  console.log(`Domaines à traiter : ${byDomain.size}`);
  const rows: Row[] = [];
  const aVerifier: Row[] = [];
  let refetched = 0;
  const now = new Date().toISOString();

  for (const [domaine, domainPages] of byDomain) {
    // Pages contact et profils en premier : l'email y est le mieux attribué.
    const ordered = [...domainPages].sort((a, b) => {
      const rank = (page: PageResult) =>
        /contact/i.test(page.url) ? 0 : looksLikeProfilePage(page.url) ? 1 : 2;
      return rank(a) - rank(b);
    });

    const fullText = ordered.map((page) => page.contenu_texte).join(" ");
    const cabinet = cabinetName(domaine, ordered);
    const typeCible = guessProfessionalType(fullText, domaine);
    const specialites = findSpecialities(fullText).join(" ; ");
    const telephone = findPhone(fullText);
    const personnalisation = buildPersonalisation(ordered);
    const site = siteUrlByDomain.get(domaine) ?? ordered[0]?.url ?? "";

    interface Candidate extends EmailHit { pageUrl: string; jsonLdName?: { prenom: string; nom: string; fonction: string } }
    const candidates: Candidate[] = [];

    for (const page of ordered) {
      for (const hit of findEmailsInText(page.contenu_texte)) {
        if (!candidates.some((item) => item.email === hit.email)) {
          candidates.push({ ...hit, pageUrl: page.url });
        }
      }
    }

    // Le texte stocké ne contient ni mailto: ni JSON-LD : on ne retélécharge
    // que si rien n'a été trouvé, pour limiter les requêtes.
    if (candidates.length === 0) {
      refetched += 1;
      console.log(`[${domaine}] aucun email dans le texte — relecture du HTML`);
      for (const { url, html } of await refetchHtml(ordered)) {
        const extraction = extractFromHtml(html);
        for (const hit of extraction.emails) {
          if (candidates.some((item) => item.email === hit.email)) continue;
          const person = extraction.personnes.find((entry) => entry.email === hit.email);
          candidates.push({
            ...hit,
            pageUrl: url,
            jsonLdName: person
              ? { prenom: person.prenom, nom: person.nom, fonction: person.fonction }
              : undefined
          });
        }
      }
    }

    if (candidates.length === 0) {
      const row: Row = {
        id: domaine, type_cible: typeCible, cabinet, prenom: "", nom: "", fonction: "",
        specialites, email: "", type_email: "non_attribue", telephone, site,
        profil_url: "", source_email_url: "", personnalisation: personnalisation.texte,
        source_personnalisation_url: personnalisation.url, niveau_confiance: "faible",
        date_collecte: now
      };
      aVerifier.push(row);
      console.log(`[${domaine}] aucun email trouvé`);
      continue;
    }

    for (const candidate of candidates) {
      const surLeDomaine = emailMatchesSite(candidate.email, domaine);
      const typeEmail = classifyEmail(candidate.email);
      const pageProfil = looksLikeProfilePage(candidate.pageUrl);

      const fromJsonLd = candidate.jsonLdName;
      const fromContext = findLawyerNames(candidate.contexte)[0];
      const fromEmail = typeEmail === "nominatif" ? namesFromEmail(candidate.email) : null;
      const names = fromJsonLd ?? fromContext ?? fromEmail ?? { prenom: "", nom: "" };
      const fonction = fromJsonLd?.fonction || findFunction(candidate.contexte);

      // Un nom reconstruit depuis la partie locale ne vaut pas un nom lu sur la
      // page : il ne peut pas à lui seul justifier une confiance élevée.
      const nomVerifie = Boolean(
        (fromJsonLd?.prenom && fromJsonLd?.nom) || (fromContext?.prenom && fromContext?.nom)
      );
      const niveau = scoreConfidence({
        source: candidate.source,
        typeEmail,
        surLeDomaine,
        pageProfil,
        nomTrouve: nomVerifie
      });

      const row: Row = {
        id: `${domaine}|${candidate.email}`,
        type_cible: typeCible,
        cabinet,
        prenom: names.prenom,
        nom: names.nom,
        fonction,
        specialites,
        email: candidate.email,
        type_email: typeEmail,
        telephone,
        site,
        profil_url: pageProfil ? candidate.pageUrl : "",
        source_email_url: candidate.pageUrl,
        personnalisation: personnalisation.texte,
        source_personnalisation_url: personnalisation.url,
        niveau_confiance: niveau,
        date_collecte: now
      };
      (niveau === "faible" ? aVerifier : rows).push(row);
    }
  }

  // Déduplication : un email n'apparaît qu'une fois ; sur un même domaine, une
  // adresse générique est écartée dès qu'une adresse nominative existe.
  const byEmail = new Map<string, Row>();
  const order = { eleve: 0, moyen: 1, faible: 2 } as const;
  for (const row of rows) {
    const existing = byEmail.get(row.email);
    if (!existing || order[row.niveau_confiance as keyof typeof order] < order[existing.niveau_confiance as keyof typeof order]) {
      byEmail.set(row.email, row);
    }
  }
  const uniqueByEmail = [...byEmail.values()];
  const domainsWithNominative = new Set(
    uniqueByEmail.filter((row) => row.type_email === "nominatif").map((row) => row.id.split("|")[0])
  );
  const finalRows = uniqueByEmail.filter(
    (row) => row.type_email === "nominatif" || !domainsWithNominative.has(row.id.split("|")[0])
  );
  const dropped = uniqueByEmail.length - finalRows.length;

  finalRows.sort((a, b) => a.cabinet.localeCompare(b.cabinet) || a.email.localeCompare(b.email));
  await fs.mkdir(path.dirname(config.prospectsFile), { recursive: true });
  await writeCsv(config.prospectsFile, headers, finalRows as unknown as Record<string, unknown>[]);
  await writeCsv(config.aVerifierFile, headers, aVerifier as unknown as Record<string, unknown>[]);

  const count = (type: string) => finalRows.filter((row) => row.type_email === type).length;
  console.log(`\n=== Résumé ===`);
  console.log(`Domaines traités : ${byDomain.size}`);
  console.log(`Domaines retéléchargés faute d'email dans le texte : ${refetched}`);
  console.log(`Prospects retenus : ${finalRows.length}`);
  console.log(`  emails nominatifs : ${count("nominatif")}`);
  console.log(`  emails génériques : ${count("generique")}`);
  console.log(`  emails non attribués : ${count("non_attribue")}`);
  console.log(`Confiance élevée : ${finalRows.filter((row) => row.niveau_confiance === "eleve").length}`);
  console.log(`Confiance moyenne : ${finalRows.filter((row) => row.niveau_confiance === "moyen").length}`);
  console.log(`Génériques écartés au profit d'une adresse nominative : ${dropped}`);
  console.log(`À vérifier : ${aVerifier.length}`);
  console.log(`\nFichiers :`);
  console.log(`  ${config.prospectsFile}`);
  console.log(`  ${config.aVerifierFile}`);
}

main().catch((error) => {
  console.error(`Échec : ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
});
