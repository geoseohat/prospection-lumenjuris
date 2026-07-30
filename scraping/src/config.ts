import "dotenv/config";
import path from "node:path";

export const projectRoot = process.cwd();

function positiveInteger(name: string, fallback: number): number {
  const raw = process.env[name];
  if (!raw) return fallback;
  const parsed = Number(raw);
  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new Error(`${name} doit être un entier positif ou nul.`);
  }
  return parsed;
}

function boolean(name: string, fallback: boolean): boolean {
  const raw = process.env[name]?.trim().toLowerCase();
  if (raw === undefined || raw === "") return fallback;
  if (["true", "1", "oui", "yes"].includes(raw)) return true;
  if (["false", "0", "non", "no"].includes(raw)) return false;
  throw new Error(`${name} doit valoir true ou false.`);
}

function list(name: string): string[] {
  return (process.env[name] ?? "")
    .split(/[,;\s]+/)
    .map((value) => value.trim().toLowerCase())
    .filter(Boolean);
}

export const config = {
  serpApiKey: process.env.SERPAPI_API_KEY?.trim() ?? "",
  scrapeDoApiKey: process.env.SCRAPEDO_API_KEY?.trim() ?? "",
  serpApiLimit: positiveInteger("SERPAPI_REQUEST_LIMIT", 249),
  scrapeDoLimit: positiveInteger("SCRAPEDO_REQUEST_LIMIT", 1000),
  searchesFile: path.join(projectRoot, "recherches.csv"),
  sitesFile: path.join(projectRoot, "sites.csv"),
  usageFile: path.join(projectRoot, "results", "api-usage.json"),
  excludedDomainsFile: path.join(projectRoot, "config", "excluded-domains.json"),
  pagesFile: path.join(projectRoot, "results", "pages.csv"),
  crawl: {
    userAgent: "LumenJurisProspection",
    httpUserAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " +
      "Chrome/126.0.0.0 Safari/537.36 LumenJurisProspection/1.0",
    maxPagesPerDomain: positiveInteger("CRAWL_MAX_PAGES", 4),
    concurrency: positiveInteger("CRAWL_CONCURRENCY", 2),
    timeoutMs: positiveInteger("CRAWL_TIMEOUT_MS", 15_000),
    delayMs: positiveInteger("CRAWL_DELAY_MS", 1_000),
    // En deçà de ce volume de texte, on tente Playwright si disponible.
    minTextLength: positiveInteger("CRAWL_MIN_TEXT", 400)
  },

  // Étape 3 — garde-fous d'envoi. dryRun et requireManualApproval sont volontairement
  // à true par défaut : une variable absente ou mal orthographiée ne doit jamais
  // ouvrir l'envoi réel.
  dryRun: boolean("DRY_RUN", true),
  requireManualApproval: boolean("REQUIRE_MANUAL_APPROVAL", true),
  testRecipients: list("TEST_RECIPIENTS"),
  openAiKey: process.env.OPENAI_API_KEY?.trim() ?? "",
  openAiModel: process.env.OPENAI_MODEL?.trim() || "gpt-4.1-mini",
  googleClientId: process.env.GOOGLE_CLIENT_ID?.trim() ?? "",
  googleClientSecret: process.env.GOOGLE_CLIENT_SECRET?.trim() ?? "",
  googleRedirectPort: positiveInteger("GOOGLE_REDIRECT_PORT", 53_682),
  sheetId: process.env.GOOGLE_SHEET_ID?.trim() ?? "",
  sheetTab: process.env.GOOGLE_SHEET_TAB?.trim() || "Feuille 1",

  tokensDir: path.join(projectRoot, "tokens"),
  sendersFile: path.join(projectRoot, "config", "senders.json"),
  prospectsFile: path.join(projectRoot, "results", "prospects.csv"),
  aVerifierFile: path.join(projectRoot, "results", "a-verifier.csv"),
  queueFile: path.join(projectRoot, "results", "email-queue.csv"),
  optOutFile: path.join(projectRoot, "results", "opt-out.csv"),
  emailLogFile: path.join(projectRoot, "results", "email-log.csv")
};
