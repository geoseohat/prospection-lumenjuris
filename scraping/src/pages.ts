import * as cheerio from "cheerio";

// Ordre décroissant d'intérêt pour la prospection.
export const priorityKeywords: string[] = [
  "contact",
  "equipe", "équipe", "team",
  "avocat", "avocats",
  "associe", "associé", "associes", "associés",
  "cabinet",
  "expertise", "expertises",
  "competence", "compétence", "competences", "compétences",
  "droit-des-contrats", "droit des contrats",
  "droit-commercial", "droit commercial",
  "droit-des-affaires", "droit des affaires",
  "contrats-informatiques", "contrats informatiques",
  "publication", "publications",
  "actualite", "actualité", "actualites", "actualités",
  "mentions-legales", "mentions légales", "mentions legales"
];

const ignoredExtensions = [
  ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".zip", ".doc",
  ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".mp4", ".mp3", ".ics", ".css", ".js"
];

function stripAccents(value: string): string {
  return value.normalize("NFD").replace(/\p{Diacritic}/gu, "");
}

// Plus le mot-clé est haut dans la liste, plus le score est élevé.
export function scoreLink(href: string, anchorText: string): number {
  const haystack = stripAccents(`${href} ${anchorText}`.toLowerCase());
  let best = 0;
  priorityKeywords.forEach((keyword, index) => {
    const needle = stripAccents(keyword.toLowerCase());
    if (haystack.includes(needle)) {
      best = Math.max(best, priorityKeywords.length - index);
    }
  });
  return best;
}

// Clé de déduplication : ignore www, la casse du domaine et le slash final.
export function visitKey(rawUrl: string): string {
  try {
    const parsed = new URL(rawUrl);
    const host = parsed.hostname.toLowerCase().replace(/^www\./, "");
    const pathname = parsed.pathname.replace(/\/+$/, "") || "/";
    return `${host}${pathname}${parsed.search}`;
  } catch {
    return rawUrl;
  }
}

// Une même page atteinte par deux URL (slash final, www) ne compte qu'une fois.
export function dedupePages<T extends { domaine: string; url: string }>(rows: T[]): {
  rows: T[];
  duplicatesRemoved: number;
} {
  const seen = new Map<string, T>();
  for (const row of rows) {
    const key = `${row.domaine}|${visitKey(row.url)}`;
    if (!seen.has(key)) seen.set(key, row);
  }
  return { rows: [...seen.values()], duplicatesRemoved: rows.length - seen.size };
}

export interface InternalLink {
  url: string;
  score: number;
}

export function extractInternalLinks(html: string, pageUrl: string, domain: string): InternalLink[] {
  const $ = cheerio.load(html);
  const seen = new Map<string, InternalLink>();

  $("a[href]").each((_, element) => {
    const href = $(element).attr("href") ?? "";
    if (!href || href.startsWith("#") || /^(mailto|tel|javascript):/i.test(href)) return;

    let parsed: URL;
    try {
      parsed = new URL(href, pageUrl);
    } catch {
      return;
    }
    if (!["http:", "https:"].includes(parsed.protocol)) return;

    const host = parsed.hostname.toLowerCase().replace(/^www\./, "");
    // Reste sur le même domaine, sous-domaines inclus.
    if (host !== domain && !host.endsWith(`.${domain}`)) return;

    const lowerPath = parsed.pathname.toLowerCase();
    if (ignoredExtensions.some((extension) => lowerPath.endsWith(extension))) return;

    parsed.hash = "";
    const url = parsed.toString();
    const score = scoreLink(parsed.pathname + parsed.search, $(element).text());
    const existing = seen.get(url);
    if (!existing || score > existing.score) seen.set(url, { url, score });
  });

  return [...seen.values()].sort((a, b) => b.score - a.score || a.url.localeCompare(b.url));
}

export function extractTitle(html: string): string {
  const $ = cheerio.load(html);
  const title = $("title").first().text().trim();
  return title || $("h1").first().text().trim();
}

export function extractText(html: string, maxLength = 12_000): string {
  const $ = cheerio.load(html);
  $("script, style, noscript, svg, iframe").remove();
  const text = $("body").text().replace(/\s+/g, " ").trim();
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text;
}
