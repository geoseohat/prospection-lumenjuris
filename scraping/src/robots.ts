import type { RobotsRules } from "./types.js";

export const emptyRules: RobotsRules = { allow: [], disallow: [], sitemaps: [], fetched: false };

// Retient les groupes visant notre agent, sinon ceux visant "*".
export function parseRobots(content: string, userAgent: string): RobotsRules {
  const agent = userAgent.toLowerCase();
  const groups = new Map<string, { allow: string[]; disallow: string[] }>();
  const sitemaps: string[] = [];
  let currentAgents: string[] = [];
  let previousWasAgent = false;

  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.split("#")[0].trim();
    if (!line) continue;
    const separator = line.indexOf(":");
    if (separator === -1) continue;
    const field = line.slice(0, separator).trim().toLowerCase();
    const value = line.slice(separator + 1).trim();

    if (field === "sitemap") {
      if (value) sitemaps.push(value);
      continue;
    }
    if (field === "user-agent") {
      if (!previousWasAgent) currentAgents = [];
      currentAgents.push(value.toLowerCase());
      previousWasAgent = true;
      continue;
    }
    previousWasAgent = false;
    if (field !== "allow" && field !== "disallow") continue;
    for (const name of currentAgents) {
      const group = groups.get(name) ?? { allow: [], disallow: [] };
      // "Disallow:" vide signifie "tout autoriser" : on ignore la règle.
      if (value) group[field].push(value);
      groups.set(name, group);
    }
  }

  const selected = groups.get(agent) ?? groups.get("*") ?? { allow: [], disallow: [] };
  return { ...selected, sitemaps, fetched: true };
}

function matchLength(path: string, rule: string): number {
  // Gère les jokers * et l'ancre de fin $.
  if (!rule.includes("*") && !rule.endsWith("$")) {
    return path.startsWith(rule) ? rule.length : -1;
  }
  const anchored = rule.endsWith("$");
  const body = anchored ? rule.slice(0, -1) : rule;
  const pattern = body.split("*").map((part) => part.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join(".*");
  const regex = new RegExp(`^${pattern}${anchored ? "$" : ""}`);
  return regex.test(path) ? body.length : -1;
}

// En cas d'égalité, Allow l'emporte sur Disallow.
export function isAllowedByRobots(pathname: string, rules: RobotsRules): boolean {
  const path = pathname || "/";
  const allow = Math.max(-1, ...rules.allow.map((rule) => matchLength(path, rule)));
  const disallow = Math.max(-1, ...rules.disallow.map((rule) => matchLength(path, rule)));
  if (disallow === -1) return true;
  return allow >= disallow;
}
