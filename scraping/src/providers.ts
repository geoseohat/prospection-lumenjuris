import type { OrganicResult, ProviderName } from "./types.js";

interface ApiResponse {
  organic_results?: Array<{
    position?: number;
    title?: string;
    link?: string;
    snippet?: string;
  }>;
  error?: string;
}

function normalizeOrganicResults(payload: ApiResponse): OrganicResult[] {
  if (payload.error) throw new Error(payload.error);
  return (payload.organic_results ?? [])
    .filter((item) => item.link && item.title)
    .map((item, index) => ({
      position: item.position ?? index + 1,
      title: item.title ?? "",
      link: item.link ?? "",
      snippet: item.snippet ?? ""
    }));
}

async function requestJson(url: URL): Promise<ApiResponse> {
  const response = await fetch(url, {
    headers: { Accept: "application/json", "User-Agent": "LumenJurisProspection/1.0" },
    signal: AbortSignal.timeout(45_000)
  });
  if (!response.ok) throw new Error(`HTTP ${response.status} ${response.statusText}`);
  return await response.json() as ApiResponse;
}

export async function searchProvider(
  provider: ProviderName,
  query: string,
  apiKey: string
): Promise<OrganicResult[]> {
  if (!apiKey) throw new Error(`Clé API manquante pour ${provider}.`);
  if (provider === "serpapi") {
    // Un seul moteur renvoie toujours les mêmes premiers résultats : les gros
    // cabinets bien référencés. Alterner Google et Bing fait remonter des
    // structures différentes — Bing classe autrement, et favorise des sites
    // plus modestes.
    const moteur = Math.random() < 0.5 ? "google" : "bing";
    const url = new URL("https://serpapi.com/search");
    const parametres: Record<string, string> =
      moteur === "google"
        ? { engine: "google", q: query, api_key: apiKey, output: "json",
            google_domain: "google.fr", gl: "fr", hl: "fr" }
        : { engine: "bing", q: query, api_key: apiKey, output: "json",
            cc: "FR", mkt: "fr-FR" };
    url.search = new URLSearchParams(parametres).toString();
    console.log(`  moteur : ${moteur}`);
    return normalizeOrganicResults(await requestJson(url));
  }

  const url = new URL("https://api.scrape.do/plugin/google/search");
  url.search = new URLSearchParams({ token: apiKey, q: query, device: "desktop", start: "0" }).toString();
  return normalizeOrganicResults(await requestJson(url));
}
