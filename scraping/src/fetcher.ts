import { config } from "./config.js";
import type { FetchMethod } from "./types.js";

export interface FetchOutcome {
  html: string;
  status: number | "";
  method: FetchMethod | "";
  error: string;
  finalUrl: string;
}

function message(error: unknown): string {
  if (error instanceof Error) {
    return error.name === "TimeoutError" || error.name === "AbortError"
      ? `timeout ${config.crawl.timeoutMs} ms`
      : error.message;
  }
  return String(error);
}

// htmlOnly=false sert aux fichiers texte (robots.txt) et XML (sitemap.xml).
export async function fetchHttp(url: string, htmlOnly = true): Promise<FetchOutcome> {
  try {
    const response = await fetch(url, {
      redirect: "follow",
      headers: {
        "User-Agent": config.crawl.httpUserAgent,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9"
      },
      signal: AbortSignal.timeout(config.crawl.timeoutMs)
    });
    const contentType = response.headers.get("content-type") ?? "";
    const readable = !htmlOnly || contentType === "" || contentType.includes("html");
    const html = readable ? await response.text() : "";
    return {
      html,
      status: response.status,
      method: "http",
      finalUrl: response.url || url,
      error: response.ok ? "" : `HTTP ${response.status} ${response.statusText}`
    };
  } catch (error) {
    return { html: "", status: "", method: "http", finalUrl: url, error: message(error) };
  }
}

let playwrightState: "unknown" | "ready" | "absent" = "unknown";
let browserPromise: Promise<any> | null = null;

// Chargement paresseux : Playwright reste optionnel et n'est jamais requis au démarrage.
async function getBrowser(): Promise<any | null> {
  if (playwrightState === "absent") return null;
  if (!browserPromise) {
    browserPromise = (async () => {
      // Spécifieur indirect : le projet compile même si Playwright n'est pas installé.
      const specifier = "playwright";
      const module = await import(specifier);
      return await module.chromium.launch({ headless: true });
    })().catch((error) => {
      playwrightState = "absent";
      console.warn(`Playwright indisponible (${message(error)}). Repli sur HTTP seul.`);
      return null;
    });
  }
  const browser = await browserPromise;
  if (browser) playwrightState = "ready";
  return browser;
}

export function isPlaywrightAvailable(): boolean {
  return playwrightState !== "absent";
}

export async function fetchWithPlaywright(url: string): Promise<FetchOutcome> {
  const browser = await getBrowser();
  if (!browser) {
    return { html: "", status: "", method: "", finalUrl: url, error: "playwright absent" };
  }
  let context: any;
  try {
    context = await browser.newContext({
      userAgent: config.crawl.httpUserAgent,
      locale: "fr-FR"
    });
    const page = await context.newPage();
    const response = await page.goto(url, {
      waitUntil: "domcontentloaded",
      timeout: config.crawl.timeoutMs
    });
    const html = await page.content();
    return {
      html,
      status: response?.status() ?? "",
      method: "playwright",
      finalUrl: page.url(),
      error: ""
    };
  } catch (error) {
    return { html: "", status: "", method: "playwright", finalUrl: url, error: message(error) };
  } finally {
    await context?.close().catch(() => undefined);
  }
}

export async function closeBrowser(): Promise<void> {
  if (!browserPromise) return;
  const browser = await browserPromise.catch(() => null);
  await browser?.close().catch(() => undefined);
  browserPromise = null;
}
