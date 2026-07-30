import assert from "node:assert/strict";
import test from "node:test";
import { extractInternalLinks, extractText, extractTitle, scoreLink, visitKey } from "../src/pages.js";
import { isAllowedByRobots, parseRobots } from "../src/robots.js";

test("parseRobots retient le groupe de notre agent plutôt que le groupe générique", () => {
  const rules = parseRobots(
    [
      "User-agent: *",
      "Disallow: /",
      "",
      "User-agent: LumenJurisProspection",
      "Disallow: /admin",
      "Allow: /admin/public",
      "",
      "Sitemap: https://exemple.fr/sitemap.xml"
    ].join("\n"),
    "LumenJurisProspection"
  );
  assert.deepEqual(rules.disallow, ["/admin"]);
  assert.deepEqual(rules.sitemaps, ["https://exemple.fr/sitemap.xml"]);
  assert.equal(rules.fetched, true);
});

test("isAllowedByRobots respecte la règle la plus spécifique", () => {
  const rules = parseRobots("User-agent: *\nDisallow: /admin\nAllow: /admin/public", "LumenJurisProspection");
  assert.equal(isAllowedByRobots("/contact", rules), true);
  assert.equal(isAllowedByRobots("/admin/secret", rules), false);
  assert.equal(isAllowedByRobots("/admin/public/page", rules), true);
});

test("isAllowedByRobots gère les jokers et l'ancre de fin", () => {
  const rules = parseRobots("User-agent: *\nDisallow: /*.php$\nDisallow: /wp-admin/", "LumenJurisProspection");
  assert.equal(isAllowedByRobots("/page.php", rules), false);
  assert.equal(isAllowedByRobots("/page.php/suite", rules), true);
  assert.equal(isAllowedByRobots("/wp-admin/options", rules), false);
});

test("isAllowedByRobots autorise tout quand Disallow est vide", () => {
  const rules = parseRobots("User-agent: *\nDisallow:", "LumenJurisProspection");
  assert.equal(isAllowedByRobots("/n-importe-quoi", rules), true);
});

test("scoreLink classe contact au-dessus de mentions légales", () => {
  assert.ok(scoreLink("/contact", "Contact") > scoreLink("/mentions-legales", "Mentions légales"));
  assert.equal(scoreLink("/panier", "Panier"), 0);
});

test("extractInternalLinks reste sur le domaine et priorise les pages utiles", () => {
  const html = `
    <a href="/mentions-legales">Mentions légales</a>
    <a href="/nos-avocats">Nos avocats</a>
    <a href="/contact">Contact</a>
    <a href="https://linkedin.com/company/x">LinkedIn</a>
    <a href="/brochure.pdf">Brochure</a>
    <a href="mailto:contact@cabinet.fr">Écrire</a>
    <a href="/panier">Panier</a>
  `;
  const links = extractInternalLinks(html, "https://cabinet.fr/", "cabinet.fr");
  const urls = links.map((link) => link.url);
  assert.equal(urls[0], "https://cabinet.fr/contact");
  assert.ok(urls.includes("https://cabinet.fr/nos-avocats"));
  assert.ok(!urls.some((url) => url.includes("linkedin")));
  assert.ok(!urls.some((url) => url.endsWith(".pdf")));
  assert.equal(links.find((link) => link.url.endsWith("/panier"))?.score, 0);
});

test("extractInternalLinks accepte les sous-domaines du même domaine", () => {
  const html = `<a href="https://www.cabinet.fr/contact">Contact</a><a href="https://autre.fr/contact">X</a>`;
  const links = extractInternalLinks(html, "https://cabinet.fr/", "cabinet.fr");
  assert.deepEqual(links.map((link) => link.url), ["https://www.cabinet.fr/contact"]);
});

test("visitKey confond www, casse et slash final", () => {
  assert.equal(visitKey("https://celestial-guardian.com/contact"), visitKey("https://celestial-guardian.com/contact/"));
  assert.equal(visitKey("https://www.Lamia-Baba.fr/"), visitKey("https://lamia-baba.fr"));
  assert.notEqual(visitKey("https://cabinet.fr/equipe"), visitKey("https://cabinet.fr/contact"));
});

test("extractText et extractTitle nettoient le HTML", () => {
  const html = "<html><head><title> Cabinet  X </title></head><body><script>var a=1</script><p>Droit  des\ncontrats</p></body></html>";
  assert.equal(extractTitle(html), "Cabinet  X");
  assert.equal(extractText(html), "Droit des contrats");
});
