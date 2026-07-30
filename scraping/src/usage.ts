import fs from "node:fs/promises";
import path from "node:path";
import type { MonthlyUsage, ProviderName, UsageFile } from "./types.js";

export function monthKey(date = new Date()): string {
  return date.toISOString().slice(0, 7);
}

export async function loadUsage(filePath: string): Promise<UsageFile> {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8")) as UsageFile;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    return { months: {} };
  }
}

export function currentUsage(file: UsageFile, month = monthKey()): MonthlyUsage {
  return file.months[month] ?? { serpapi: 0, scrapedo: 0 };
}

export function selectProvider(
  usage: MonthlyUsage,
  limits: MonthlyUsage,
  availableKeys: Record<ProviderName, boolean>
): ProviderName | null {
  if (availableKeys.serpapi && usage.serpapi < limits.serpapi) return "serpapi";
  if (availableKeys.scrapedo && usage.scrapedo < limits.scrapedo) return "scrapedo";
  return null;
}

export async function reserveRequest(
  filePath: string,
  usageFile: UsageFile,
  provider: ProviderName,
  limit: number,
  month = monthKey()
): Promise<MonthlyUsage> {
  const usage = currentUsage(usageFile, month);
  if (usage[provider] >= limit) throw new Error(`Quota ${provider} atteint.`);
  const updated = { ...usage, [provider]: usage[provider] + 1 };
  usageFile.months[month] = updated;
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(usageFile, null, 2)}\n`, "utf8");
  return updated;
}
