import type { SiteResult } from "./types.js";

const directorySignals = [
  "annuaire", "classement", "comparatif", "trouver-un-avocat", "avocats/", "professionnels/",
  "mise-en-relation", "forum", "emploi", "recrutement"
];

const legalSignals = [
  "avocat", "cabinet", "juriste", "juridique", "droit", "legal", "contrat",
  "contentieux", "commercial", "affaires", "conseil", "consultant"
];

// Signaux appliqués au domaine seul : plateformes, écoles et sites d'emploi.
const platformDomainSignals = [
  "freelance", "freelances", "portage", "ecole", "ecoles", "universite", "master",
  "masters", "formation", "emploi", "job", "recrutement", "stage", "comparateur",
  "meilleurs-", "meilleur-", "top-", "annuaire", "blog"
];

// Signaux appliqués au titre seul : contenu éditorial, pas un site de praticien.
const editorialTitleSignals = [
  "fiche métier", "fiche metier", "quel est son rôle", "quel est son role",
  "définition", "definition", "c'est quoi", "qu'est-ce qu", "devenir ",
  "salaire", "comment choisir", "pourquoi faire appel", "classement",
  "meilleurs ", "top 10", "disponibles", "missions, compétences", "ou juriste"
];

export function normalizeUrl(rawUrl: string): { url: string; domain: string } | null {
  try {
    const parsed = new URL(rawUrl);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    parsed.hash = "";
    for (const key of [...parsed.searchParams.keys()]) {
      if (key.startsWith("utm_") || ["gclid", "fbclid"].includes(key)) {
        parsed.searchParams.delete(key);
      }
    }
    const domain = parsed.hostname.toLowerCase().replace(/^www\./, "");
    parsed.hostname = domain;
    return { url: parsed.toString(), domain };
  } catch {
    return null;
  }
}

export function isExcludedDomain(domain: string, excluded: string[]): boolean {
  return excluded.some((blocked) => domain === blocked || domain.endsWith(`.${blocked}`));
}

export function looksLikeOfficialRelevantSite(
  title: string,
  snippet: string,
  url: string,
  domain: string
): boolean {
  const haystack = `${title} ${snippet} ${url} ${domain}`.toLowerCase();
  const lowerDomain = domain.toLowerCase();
  const lowerTitle = title.toLowerCase();
  if (directorySignals.some((signal) => haystack.includes(signal))) return false;
  if (platformDomainSignals.some((signal) => lowerDomain.includes(signal))) return false;
  if (editorialTitleSignals.some((signal) => lowerTitle.includes(signal))) return false;
  return legalSignals.some((signal) => haystack.includes(signal));
}

export function dedupeByDomain(rows: SiteResult[]): {
  rows: SiteResult[];
  duplicatesRemoved: number;
} {
  const best = new Map<string, SiteResult>();
  for (const row of rows) {
    const existing = best.get(row.domaine);
    if (!existing || row.position < existing.position) best.set(row.domaine, row);
  }
  return { rows: [...best.values()], duplicatesRemoved: rows.length - best.size };
}
