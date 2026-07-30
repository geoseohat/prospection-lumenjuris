import * as cheerio from "cheerio";

export type EmailType = "nominatif" | "generique" | "non_attribue";
export type Confidence = "eleve" | "moyen" | "faible";

// Comptes fonctionnels à ne jamais démarcher.
const excludedLocalParts = [
  "noreply", "no-reply", "ne-pas-repondre", "webmaster", "postmaster",
  "dpo", "rgpd", "recrutement", "recrutements", "rh", "presse", "press",
  "candidature", "candidatures", "stage", "stages"
];

const technicalDomains = [
  "sentry.io", "wixpress.com", "example.com", "domain.com", "email.com",
  "votredomaine.fr", "monsite.fr", "sentry-next.wixpress.com"
];

const genericLocalParts = [
  "contact", "info", "infos", "cabinet", "secretariat", "accueil", "bonjour",
  "hello", "avocat", "avocats", "etude", "mail", "courrier", "administration"
];

const emailPattern = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;

// Deux balises collées dans le HTML produisent « Fondateurb.robelin@… ».
// On retire le mot de fonction seulement s'il reste une partie locale plausible.
const gluedPrefixes = [
  "fondateur", "fondatrice", "cofondateur", "cofondatrice", "avocate", "avocat",
  "associee", "associe", "maitre", "contact", "cabinet", "secretariat",
  "email", "mail", "courriel", "ecrire", "telephone", "adresse"
];

export function repairGluedLocalPart(email: string): string {
  const [local, domain] = email.toLowerCase().split("@");
  if (!domain) return email;
  for (const prefix of gluedPrefixes) {
    if (local === prefix || !local.startsWith(prefix)) continue;
    const rest = local.slice(prefix.length);
    // Le reste doit ressembler à un nom : « b.robelin », « marie.dupont ».
    if (/^[a-z]{1,}[._-][a-z]{2,}$/.test(rest) || /^[a-z]{3,}$/.test(rest)) {
      return `${rest}@${domain}`;
    }
  }
  return email;
}

// Rétablit les écritures destinées à tromper les robots avant toute recherche.
export function deobfuscate(text: string): string {
  return text
    .replace(/\s*[\[({<]\s*(at|arobase|a)\s*[\])}>]\s*/gi, "@")
    .replace(/\s+arobase\s+/gi, "@")
    .replace(/\s*[\[({<]\s*(dot|point)\s*[\])}>]\s*/gi, ".")
    .replace(/\s+point\s+(fr|com|net|org|eu|be|ch|law|legal)\b/gi, ".$1");
}

export function isUsableEmail(email: string): boolean {
  const value = email.toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/.test(value)) return false;
  const [local, domain] = value.split("@");
  if (excludedLocalParts.some((part) => local === part || local.startsWith(`${part}.`) || local.startsWith(`${part}-`))) {
    return false;
  }
  if (technicalDomains.some((blocked) => domain === blocked || domain.endsWith(`.${blocked}`))) return false;
  if (/\.(png|jpe?g|gif|webp|svg|css|js|woff2?)$/.test(domain)) return false;
  // Une adresse ne se termine jamais par un point ou un tiret.
  if (/[.-]$/.test(local) || /^[.-]/.test(local)) return false;
  return true;
}

export function classifyEmail(email: string): EmailType {
  const local = email.toLowerCase().split("@")[0];
  if (genericLocalParts.some((part) => local === part || local.startsWith(`${part}.`))) return "generique";
  // prenom.nom@ ou p.nom@ : forme nominative la plus courante en cabinet.
  if (/^[a-z]+[._-][a-z]+$/.test(local)) return "nominatif";
  if (/^[a-z]\.[a-z]+$/.test(local)) return "nominatif";
  if (genericLocalParts.includes(local)) return "generique";
  if (/^[a-z]{3,}$/.test(local)) return "non_attribue";
  return "non_attribue";
}

// Deux mots capitalisés après Maître / Me : le motif le plus fiable en français.
export function findLawyerNames(text: string): Array<{ prenom: string; nom: string }> {
  const results: Array<{ prenom: string; nom: string }> = [];
  const pattern = /\b(?:Ma[iî]tre|Me)\.?\s+([A-ZÉÈÀÂÎÔÛÇ][a-zéèêàâîïôûùç-]{1,20})\s+([A-ZÉÈÀÂÎÔÛÇ][A-Za-zÉÈÀÂÎÔÛÇéèêàâîïôûùç'-]{1,25})/g;
  for (const match of text.matchAll(pattern)) {
    results.push({ prenom: match[1], nom: match[2] });
  }
  return results;
}

// Déduit un nom depuis la partie locale prenom.nom : l'adresse est réelle,
// seule la coupure est interprétée, d'où un niveau de confiance réduit.
export function namesFromEmail(email: string): { prenom: string; nom: string } | null {
  const local = email.toLowerCase().split("@")[0];
  // Trois lettres minimum : « as.durouchoux » sont des initiales, pas un prénom.
  const match = /^([a-z]{3,})[._-]([a-z]{3,})$/.exec(local);
  if (!match) return null;
  const capitalize = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);
  return { prenom: capitalize(match[1]), nom: capitalize(match[2]) };
}

export function findPhone(text: string): string {
  const patterns = [
    /\+33\s?\(?0?\)?[\s.-]?[1-9](?:[\s.-]?\d{2}){4}/,
    /\b0[1-9](?:[\s.-]?\d{2}){4}\b/
  ];
  for (const pattern of patterns) {
    const match = pattern.exec(text);
    if (match) return match[0].replace(/\s+/g, " ").trim();
  }
  return "";
}

export interface EmailHit {
  email: string;
  source: "mailto" | "jsonld" | "texte";
  contexte: string;
}

function contextAround(text: string, email: string): string {
  const index = text.toLowerCase().indexOf(email.toLowerCase());
  if (index < 0) return "";
  return text.slice(Math.max(0, index - 140), index + 140).replace(/\s+/g, " ").trim();
}

export function findEmailsInText(rawText: string): EmailHit[] {
  const text = deobfuscate(rawText);
  const hits = new Map<string, EmailHit>();
  for (const candidate of text.match(emailPattern) ?? []) {
    const email = repairGluedLocalPart(candidate.toLowerCase());
    if (!isUsableEmail(email) || hits.has(email)) continue;
    // Le contexte se cherche sur la forme brute, seule présente dans la page.
    hits.set(email, { email, source: "texte", contexte: contextAround(text, candidate) });
  }
  return [...hits.values()];
}

export interface HtmlExtraction {
  emails: EmailHit[];
  personnes: Array<{ prenom: string; nom: string; fonction: string; email: string }>;
  telephone: string;
}

function walkJsonLd(node: unknown, collect: (value: Record<string, unknown>) => void): void {
  if (Array.isArray(node)) {
    for (const item of node) walkJsonLd(item, collect);
    return;
  }
  if (!node || typeof node !== "object") return;
  const value = node as Record<string, unknown>;
  collect(value);
  for (const child of Object.values(value)) walkJsonLd(child, collect);
}

export function extractFromHtml(html: string): HtmlExtraction {
  const $ = cheerio.load(html);
  const emails = new Map<string, EmailHit>();
  const personnes: HtmlExtraction["personnes"] = [];

  $('a[href^="mailto:"]').each((_, element) => {
    const href = $(element).attr("href") ?? "";
    const decoded = decodeURIComponent(href.slice(7).split("?")[0]).trim().toLowerCase();
    const raw = repairGluedLocalPart(decoded);
    if (!isUsableEmail(raw) || emails.has(raw)) return;
    const contexte = $(element).closest("li, div, section, article, td, p").first().text()
      .replace(/\s+/g, " ").trim().slice(0, 280) || $(element).text().trim();
    emails.set(raw, { email: raw, source: "mailto", contexte });
  });

  $('script[type="application/ld+json"]').each((_, element) => {
    const raw = $(element).contents().text();
    if (!raw.trim()) return;
    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return;
    }
    walkJsonLd(parsed, (node) => {
      const type = String(node["@type"] ?? "");
      const email = String(node.email ?? "").replace(/^mailto:/i, "").trim().toLowerCase();
      if (email && isUsableEmail(email) && !emails.has(email)) {
        emails.set(email, { email, source: "jsonld", contexte: `JSON-LD ${type || "objet"}` });
      }
      if (/Person/i.test(type)) {
        const fullName = String(node.name ?? "").trim();
        const given = String(node.givenName ?? "").trim();
        const family = String(node.familyName ?? "").trim();
        const parts = fullName.split(/\s+/);
        personnes.push({
          prenom: given || parts[0] || "",
          nom: family || parts.slice(1).join(" ") || "",
          fonction: String(node.jobTitle ?? "").trim(),
          email
        });
      }
    });
  });

  const bodyText = $("body").text();
  for (const hit of findEmailsInText(bodyText)) {
    if (!emails.has(hit.email)) emails.set(hit.email, hit);
  }

  return { emails: [...emails.values()], personnes, telephone: findPhone(bodyText) };
}

// L'email hébergé sur le domaine du cabinet est le signal le plus fort.
export function emailMatchesSite(email: string, siteDomain: string): boolean {
  const emailDomain = email.toLowerCase().split("@")[1] ?? "";
  const root = siteDomain.toLowerCase().replace(/^www\./, "");
  return emailDomain === root || emailDomain.endsWith(`.${root}`) || root.endsWith(`.${emailDomain}`);
}

export function scoreConfidence(input: {
  source: EmailHit["source"];
  typeEmail: EmailType;
  surLeDomaine: boolean;
  pageProfil: boolean;
  nomTrouve: boolean;
}): Confidence {
  if (!input.surLeDomaine) return "faible";
  if (input.source === "jsonld" && input.nomTrouve) return "eleve";
  if (input.pageProfil && input.typeEmail === "nominatif" && input.nomTrouve) return "eleve";
  if (input.typeEmail === "nominatif") return "moyen";
  if (input.typeEmail === "generique" && input.source === "mailto") return "moyen";
  if (input.typeEmail === "generique") return "moyen";
  return "faible";
}

const profileHints = ["equipe", "avocat", "associe", "profil", "team", "notre-cabinet", "qui-sommes"];

export function looksLikeProfilePage(url: string): boolean {
  const value = url.toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "");
  return profileHints.some((hint) => value.includes(hint));
}

export function guessProfessionalType(text: string, siteDomain: string): string {
  const haystack = `${text} ${siteDomain}`.toLowerCase();
  if (/juriste\s+ind[ée]pendant|juriste\s+freelance/.test(haystack)) return "juriste independant";
  if (/consultant\s+juridique/.test(haystack)) return "consultant juridique";
  if (/\bavocats?\b/.test(haystack)) {
    return /cabinet|associ[ée]s|selarl|scp\b|aarpi/.test(haystack) ? "cabinet" : "avocat";
  }
  if (/expert[- ]comptable|notaire|conseil\s+en\s+propri[ée]t[ée]/.test(haystack)) return "prescripteur";
  return "autre professionnel du droit";
}

const specialityLabels: Array<[string, RegExp]> = [
  ["droit des contrats", /droit\s+des\s+contrats|droit\s+contractuel/i],
  ["contentieux contractuel", /contentieux\s+contractuel|litiges?\s+contractuels?/i],
  ["droit commercial", /droit\s+commercial/i],
  ["droit des affaires", /droit\s+des\s+affaires/i],
  ["contrats informatiques", /contrats?\s+informatiques?|droit\s+de\s+l['’]informatique|droit\s+du\s+num[ée]rique/i],
  ["droit des sociétés", /droit\s+des\s+soci[ée]t[ée]s/i],
  ["propriété intellectuelle", /propri[ée]t[ée]\s+intellectuelle/i],
  ["droit du travail", /droit\s+du\s+travail|droit\s+social/i]
];

export function findSpecialities(text: string): string[] {
  return specialityLabels.filter(([, pattern]) => pattern.test(text)).map(([label]) => label);
}
