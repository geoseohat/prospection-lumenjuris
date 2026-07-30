import assert from "node:assert/strict";
import test from "node:test";
import {
  dedupeByDomain, isExcludedDomain, looksLikeOfficialRelevantSite, normalizeUrl
} from "../src/filters.js";
import type { SiteResult } from "../src/types.js";

test("normalizeUrl retire www, fragment et paramètres de suivi", () => {
  const result = normalizeUrl("https://www.Exemple.fr/page?utm_source=test&id=2#contact");
  assert.deepEqual(result, {
    url: "https://exemple.fr/page?id=2",
    domain: "exemple.fr"
  });
});

test("normalizeUrl refuse les protocoles non HTTP", () => {
  assert.equal(normalizeUrl("mailto:contact@example.fr"), null);
});

test("isExcludedDomain bloque le domaine et ses sous-domaines", () => {
  assert.equal(isExcludedDomain("fr.linkedin.com", ["linkedin.com"]), true);
  assert.equal(isExcludedDomain("cabinet-avocat.fr", ["linkedin.com"]), false);
});

test("looksLikeOfficialRelevantSite conserve un site de praticien", () => {
  assert.equal(
    looksLikeOfficialRelevantSite(
      "Avocat en droit des contrats à Paris",
      "Cabinet dédié au droit contractuel.",
      "https://kibleravocat.com/droit-des-contrats",
      "kibleravocat.com"
    ),
    true
  );
});

test("looksLikeOfficialRelevantSite conserve un juriste freelance dont le titre mentionne freelance", () => {
  assert.equal(
    looksLikeOfficialRelevantSite(
      "Juriste freelance indépendant à Lille",
      "Accompagnement contractuel des entreprises.",
      "https://view-avocats.fr/",
      "view-avocats.fr"
    ),
    true
  );
});

test("looksLikeOfficialRelevantSite écarte les écoles, plateformes et portage via le domaine", () => {
  const cases: Array<[string, string]> = [
    ["esam-ecoles.com", "Fiche métier Consultant juridique"],
    ["lesbonsfreelances.com", "Juriste Freelance, Paris (75)"],
    ["meilleurs-masters.com", "Consultant en droit des affaires"],
    ["leblogdudirigeant.com", "Le juriste indépendant"],
    ["abcportage.fr", "Consultant Juridique"]
  ];
  for (const [domain, title] of cases) {
    assert.equal(
      looksLikeOfficialRelevantSite(title, "droit des contrats", `https://${domain}/page`, domain),
      false,
      domain
    );
  }
});

test("looksLikeOfficialRelevantSite écarte les contenus éditoriaux via le titre", () => {
  assert.equal(
    looksLikeOfficialRelevantSite(
      "Fiche métier : juriste en droit des contrats",
      "",
      "https://exemple.fr/metiers",
      "exemple.fr"
    ),
    false
  );
  assert.equal(
    looksLikeOfficialRelevantSite(
      "47 freelances « juriste d'entreprise » disponibles",
      "droit des contrats",
      "https://exemple-plateforme.fr/",
      "exemple-plateforme.fr"
    ),
    false
  );
});

test("dedupeByDomain conserve la meilleure position", () => {
  const base: SiteResult = {
    type_cible: "avocat", requete: "test", titre: "Cabinet", url: "https://cabinet.fr",
    domaine: "cabinet.fr", description: "", position: 8, moteur: "google",
    source_api: "serpapi", date_collecte: "2026-07-30T00:00:00.000Z"
  };
  const result = dedupeByDomain([base, { ...base, position: 2, url: "https://cabinet.fr/contrats" }]);
  assert.equal(result.duplicatesRemoved, 1);
  assert.equal(result.rows[0].position, 2);
});
