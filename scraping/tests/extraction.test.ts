import assert from "node:assert/strict";
import test from "node:test";
import {
  classifyEmail, deobfuscate, emailMatchesSite, extractFromHtml, findEmailsInText,
  findLawyerNames, findPhone, findSpecialities, guessProfessionalType, isUsableEmail,
  namesFromEmail, repairGluedLocalPart, scoreConfidence
} from "../src/extraction.js";

test("repairGluedLocalPart retire un mot de fonction collé à l'adresse", () => {
  assert.equal(repairGluedLocalPart("fondateurb.robelin@novlaw.fr"), "b.robelin@novlaw.fr");
  assert.equal(repairGluedLocalPart("avocatmarie.dupont@cabinet.fr"), "marie.dupont@cabinet.fr");
  // Une adresse générique légitime ne doit pas être amputée.
  assert.equal(repairGluedLocalPart("avocat@cabinet.fr"), "avocat@cabinet.fr");
  assert.equal(repairGluedLocalPart("contact@cabinet.fr"), "contact@cabinet.fr");
  assert.equal(repairGluedLocalPart("marie.dupont@cabinet.fr"), "marie.dupont@cabinet.fr");
});

test("namesFromEmail ne confond pas des initiales avec un prénom", () => {
  assert.equal(namesFromEmail("as.durouchoux@cabinet.fr"), null);
  assert.equal(namesFromEmail("m.delcroix@cabinet.fr"), null);
  assert.deepEqual(namesFromEmail("marie.dupont@cabinet.fr"), { prenom: "Marie", nom: "Dupont" });
});

test("deobfuscate reconnaît [at], (at) et arobase", () => {
  assert.match(deobfuscate("contact [at] cabinet.fr"), /contact@cabinet\.fr/);
  assert.match(deobfuscate("contact (at) cabinet.fr"), /contact@cabinet\.fr/);
  assert.match(deobfuscate("contact arobase cabinet.fr"), /contact@cabinet\.fr/);
  assert.match(deobfuscate("marie [at] cabinet [dot] fr"), /marie@cabinet\.fr/);
});

test("isUsableEmail exclut les comptes fonctionnels", () => {
  for (const local of ["noreply", "no-reply", "webmaster", "dpo", "recrutement", "presse"]) {
    assert.equal(isUsableEmail(`${local}@cabinet.fr`), false, local);
  }
  assert.equal(isUsableEmail("marie.dupont@cabinet.fr"), true);
  assert.equal(isUsableEmail("contact@cabinet.fr"), true);
  assert.equal(isUsableEmail("truc@sentry.wixpress.com"), false);
  assert.equal(isUsableEmail("pas-une-adresse"), false);
});

test("classifyEmail distingue nominatif, générique et non attribué", () => {
  assert.equal(classifyEmail("marie.dupont@cabinet.fr"), "nominatif");
  assert.equal(classifyEmail("m.dupont@cabinet.fr"), "nominatif");
  assert.equal(classifyEmail("contact@cabinet.fr"), "generique");
  assert.equal(classifyEmail("secretariat@cabinet.fr"), "generique");
  assert.equal(classifyEmail("etude@cabinet.fr"), "generique");
  assert.equal(classifyEmail("xyzab@cabinet.fr"), "non_attribue");
});

test("findEmailsInText ne remonte jamais une adresse absente", () => {
  const hits = findEmailsInText("Le cabinet intervient en droit des contrats. Téléphone 01 42 00 00 00.");
  assert.deepEqual(hits, []);
});

test("findEmailsInText retrouve une adresse obfusquée avec son contexte", () => {
  const hits = findEmailsInText("Maître Claire Bernard, avocate associée — claire.bernard [at] cabinet-bernard.fr");
  assert.equal(hits.length, 1);
  assert.equal(hits[0].email, "claire.bernard@cabinet-bernard.fr");
  assert.match(hits[0].contexte, /Claire Bernard/);
});

test("findLawyerNames lit le motif Maître Prénom Nom", () => {
  assert.deepEqual(findLawyerNames("Contactez Maître Claire Bernard au cabinet")[0], {
    prenom: "Claire", nom: "Bernard"
  });
  assert.deepEqual(findLawyerNames("aucun nom ici"), []);
});

test("namesFromEmail ne déduit un nom que d'une partie locale explicite", () => {
  assert.deepEqual(namesFromEmail("claire.bernard@cabinet.fr"), { prenom: "Claire", nom: "Bernard" });
  assert.equal(namesFromEmail("contact@cabinet.fr"), null);
});

test("findPhone reconnaît les formats français", () => {
  assert.equal(findPhone("Tel : 01 42 65 00 00"), "01 42 65 00 00");
  assert.equal(findPhone("+33 1 42 65 00 00"), "+33 1 42 65 00 00");
  assert.equal(findPhone("pas de numéro"), "");
});

test("extractFromHtml lit les mailto et le JSON-LD", () => {
  const html = `
    <html><head>
      <script type="application/ld+json">
      {"@type":"Person","name":"Claire Bernard","jobTitle":"Avocate associée","email":"claire.bernard@cabinet.fr"}
      </script>
    </head><body>
      <li>Maître Paul Martin — <a href="mailto:paul.martin@cabinet.fr">écrire</a></li>
      <a href="mailto:noreply@cabinet.fr">ne pas répondre</a>
      <p>Tel 01 42 65 00 00</p>
    </body></html>`;
  const result = extractFromHtml(html);
  const emails = result.emails.map((hit) => hit.email).sort();
  assert.deepEqual(emails, ["claire.bernard@cabinet.fr", "paul.martin@cabinet.fr"]);
  assert.equal(result.emails.find((hit) => hit.email.startsWith("paul"))?.source, "mailto");
  assert.equal(result.personnes[0].nom, "Bernard");
  assert.equal(result.personnes[0].fonction, "Avocate associée");
  assert.equal(result.telephone, "01 42 65 00 00");
});

test("emailMatchesSite compare l'adresse au domaine du site", () => {
  assert.equal(emailMatchesSite("contact@cabinet.fr", "cabinet.fr"), true);
  assert.equal(emailMatchesSite("contact@paris.cabinet.fr", "cabinet.fr"), true);
  assert.equal(emailMatchesSite("cabinet@gmail.com", "cabinet.fr"), false);
});

test("scoreConfidence rétrograde une adresse hors domaine", () => {
  assert.equal(scoreConfidence({
    source: "mailto", typeEmail: "nominatif", surLeDomaine: false, pageProfil: true, nomTrouve: true
  }), "faible");
  assert.equal(scoreConfidence({
    source: "jsonld", typeEmail: "nominatif", surLeDomaine: true, pageProfil: false, nomTrouve: true
  }), "eleve");
  assert.equal(scoreConfidence({
    source: "texte", typeEmail: "generique", surLeDomaine: true, pageProfil: false, nomTrouve: false
  }), "moyen");
});

test("guessProfessionalType et findSpecialities restent factuels", () => {
  assert.equal(guessProfessionalType("Juriste indépendant en droit des contrats", "view.fr"), "juriste independant");
  assert.equal(guessProfessionalType("Cabinet d'avocats associés", "cab.fr"), "cabinet");
  assert.equal(guessProfessionalType("boulangerie", "pain.fr"), "autre professionnel du droit");
  assert.deepEqual(
    findSpecialities("Nous intervenons en droit des contrats et en droit commercial."),
    ["droit des contrats", "droit commercial"]
  );
});
