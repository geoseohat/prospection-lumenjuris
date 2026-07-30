"""
Routine quotidienne de prospection Lumen Juris.

    python routine.py            execution complete (recolte puis envoi)
    python routine.py --etat     etat du stock et des quotas, sans rien envoyer
    python routine.py --recolte  constitue le stock seulement
    python routine.py --envoi    envoie seulement
    python routine.py --simule   affiche ce qui serait envoye, sans rien envoyer

Chaque matin :
  1. lit ACTIF dans l'onglet Config du Google Sheet, s'arrete si ce n'est pas oui
  2. complete le stock jusqu'a STOCK_CIBLE leads (recherche, visite, extraction)
  3. envoie MAX_PAR_BOITE emails par adresse expeditrice, espaces de PAUSE_MINUTES
  4. recopie la base dans le Sheet et ajoute une ligne au Journal
"""

import csv
import sys
import time
import random
import smtplib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

import base
import sheets
import requetes as generateur
from personnalisation import construire
from envoi import COMPTES, comptes_configures, se_connecter, mot_de_passe

DOSSIER = Path(__file__).parent
SCRAPING = DOSSIER / "scraping"
RECHERCHES = SCRAPING / "recherches.csv"
PROSPECTS = SCRAPING / "results" / "prospects.csv"
USAGE = SCRAPING / "results" / "api-usage.json"

# Marge de securite : on ne lance jamais plus de recherches que necessaire.
SITES_PAR_RECHERCHE = 6
RENDEMENT_EMAIL = 0.8


def npm(commande, silencieux=False):
    """Lance une commande npm du projet de scraping."""
    # npm.cmd sous Windows, npm sous Linux : la routine tourne sur les deux.
    executable = "npm.cmd" if sys.platform == "win32" else "npm"
    resultat = subprocess.run(
        [executable, "run", commande],
        cwd=SCRAPING, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if not silencieux:
        for ligne in (resultat.stdout or "").splitlines()[-12:]:
            print(f"    {ligne}")
    if resultat.returncode != 0:
        extrait = (resultat.stderr or resultat.stdout or "")[-400:]
        raise RuntimeError(f"npm run {commande} a echoue : {extrait}")
    return resultat.stdout or ""


PLAFOND_SERPAPI = 249
PLAFOND_SCRAPEDO = 1000


def quotas():
    """
    Compteurs mensuels ecrits par le projet de scraping.
    Le projet TypeScript bascule seul sur Scrape.do quand SerpApi est plein :
    la capacite reelle est donc la somme des deux, pas SerpApi seul.
    """
    import json
    try:
        donnees = json.loads(USAGE.read_text(encoding="utf-8"))
        mois = donnees.get("months", {}).get(datetime.now().strftime("%Y-%m"), {})
    except Exception:
        mois = {}
    serp = mois.get("serpapi", 0)
    scrape = mois.get("scrapedo", 0)
    return {
        "serpapi": serp,
        "scrapedo": scrape,
        "restant": (PLAFOND_SERPAPI - serp) + (PLAFOND_SCRAPEDO - scrape),
    }


def quota_serpapi():
    q = quotas()
    return q["serpapi"], PLAFOND_SERPAPI


def ecrire_recherches(combinaisons):
    with RECHERCHES.open("w", encoding="utf-8", newline="") as f:
        f.write("type_cible,requete\n")
        for cible, requete in combinaisons:
            f.write(f"{cible},{requete}\n")


def lire_prospects():
    if not PROSPECTS.exists():
        return []
    with PROSPECTS.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def recolter(cx, cible_stock):
    """Complete le stock jusqu'a cible_stock leads prets a etre contactes."""
    manquants = cible_stock - base.stock_disponible(cx)
    if manquants <= 0:
        print(f"Stock suffisant : {base.stock_disponible(cx)} leads disponibles.")
        return 0, 0

    besoin_sites = int(manquants / RENDEMENT_EMAIL) + 1
    nb_recherches = max(1, min(12, besoin_sites // SITES_PAR_RECHERCHE + 1))

    q = quotas()
    nb_recherches = min(nb_recherches, q["restant"])
    if nb_recherches <= 0:
        message = (f"Quotas epuises : SerpApi {q['serpapi']}/{PLAFOND_SERPAPI}, "
                   f"Scrape.do {q['scrapedo']}/{PLAFOND_SCRAPEDO}. "
                   f"Envoi poursuivi avec le stock existant.")
        print(message)
        base.ajouter_journal(cx, "recolte", message, erreurs=1)
        return 0, 0
    if q["serpapi"] >= PLAFOND_SERPAPI:
        print(f"SerpApi epuise ({q['serpapi']}/{PLAFOND_SERPAPI}) : bascule sur Scrape.do.")

    deja = base.requetes_deja_faites(cx)
    combinaisons = generateur.prochaines_requetes(deja, nb_recherches)
    if not combinaisons:
        print("Toutes les combinaisons ville x specialite ont ete utilisees.")
        base.ajouter_journal(cx, "recolte", "plus aucune requete disponible", erreurs=1)
        return 0, 0

    print(f"\n{manquants} lead(s) manquant(s) -> {len(combinaisons)} recherche(s) :")
    for _, requete in combinaisons:
        print(f"  - {requete}")

    ecrire_recherches(combinaisons)
    print("\n[1/3] Recherche Google")
    npm("search")
    print("[2/3] Visite des sites")
    npm("crawl")
    print("[3/3] Extraction des emails")
    npm("extract")

    for _, requete in combinaisons:
        base.marquer_requete(cx, requete)

    ajoutes = base.importer_prospects(cx, lire_prospects())
    print(f"\n{ajoutes} nouveau(x) lead(s) ajoute(s) a la base.")
    return ajoutes, len(combinaisons)


def envoyer(cx, max_par_boite, pause_minutes, max_par_domaine=3, simulation=False):
    prets, manquants = comptes_configures()
    for compte in manquants:
        print(f"[ignore] {compte['adresse']} : pas de mot de passe")
    if not prets:
        print("Aucun compte expediteur configure.")
        return 0, 0

    plan = []
    for compte in prets:
        restant = min(max_par_boite, base.quota_restant(cx, compte["cle"], max_par_boite))
        if restant <= 0:
            print(f"[plein] {compte['adresse']} : plafond des 24 h atteint")
            continue
        plan.append((compte, restant))
    if not plan:
        return 0, 0

    total = sum(restant for _, restant in plan)
    candidats = cx.execute("""
        SELECT * FROM destinataires
        WHERE etat = 'a_envoyer'
          AND email NOT IN (SELECT email FROM exclusions)
        ORDER BY CASE type_email WHEN 'nominatif' THEN 0 ELSE 1 END, ajoute_le
    """).fetchall()

    # Au plus max_par_domaine adresses par site, tous envois confondus : un
    # cabinet qui expose six adresses ne doit pas recevoir six messages.
    deja = {}
    for l in cx.execute(
        "SELECT domaine, COUNT(*) n FROM destinataires WHERE etat = 'envoye' GROUP BY domaine"
    ):
        if l["domaine"]:
            deja[l["domaine"]] = l["n"]

    lignes, compte_domaine = [], dict(deja)
    for candidat in candidats:
        domaine = candidat["domaine"] or candidat["email"].split("@")[1]
        if compte_domaine.get(domaine, 0) >= max_par_domaine:
            continue
        compte_domaine[domaine] = compte_domaine.get(domaine, 0) + 1
        lignes.append(candidat)
        if len(lignes) >= total:
            break

    ignores = len(candidats) - len(lignes)
    if ignores > 0:
        print(f"{ignores} adresse(s) mise(s) de cote : limite de {max_par_domaine} "
              f"message(s) par site atteinte.")

    if not lignes:
        print("Aucun lead a contacter.")
        return 0, 0

    print(f"\n{len(lignes)} email(s) a envoyer, un toutes les ~{pause_minutes} min.")
    print(f"Repartition : " + ", ".join(f"{c['adresse']} x{n}" for c, n in plan))

    # Alternance stricte entre les boites, dans la limite de chacune.
    file_comptes = []
    for compte, restant in plan:
        file_comptes.extend([compte] * restant)
    file_comptes.sort(key=lambda c: c["cle"])
    melange = []
    index = {c["cle"]: 0 for c, _ in plan}
    while file_comptes:
        for compte, _ in plan:
            candidats = [c for c in file_comptes if c["cle"] == compte["cle"]]
            if candidats:
                melange.append(candidats[0])
                file_comptes.remove(candidats[0])

    envoyes, erreurs = 0, 0
    for i, destinataire in enumerate(lignes):
        if i >= len(melange):
            break
        compte = melange[i]
        objet, corps, html = construire(dict(destinataire), compte)

        if simulation:
            print(f"\n--- [{i + 1}] {destinataire['email']}  <- {compte['adresse']}")
            print(f"Objet : {objet}")
            print(corps)
            continue

        try:
            from envoi import composer
            faux = {"email": destinataire["email"], "nom": destinataire["nom"] or ""}
            message = composer(compte, faux, objet, corps, html)
            with se_connecter(compte) as serveur:
                serveur.send_message(message)
            cx.execute(
                "UPDATE destinataires SET etat='envoye', compte=?, envoye_le=?, sujet=? "
                "WHERE email=?",
                (compte["cle"], base.maintenant(), objet, destinataire["email"]),
            )
            envoyes += 1
            print(f"[ok]   {destinataire['email']}  <- {compte['adresse']}")
            # Chaque envoi apparait immediatement dans le Journal du Sheet.
            sheets.journal_envoi(
                datetime.now().strftime("%Y-%m-%d %H:%M"), destinataire["email"],
                destinataire["cabinet"] or "", compte["adresse"], objet, "envoye",
            )

        except smtplib.SMTPRecipientsRefused:
            cx.execute("UPDATE destinataires SET etat='invalide' WHERE email=?",
                       (destinataire["email"],))
            cx.execute("INSERT OR IGNORE INTO exclusions VALUES (?, ?)",
                       (destinataire["email"], "adresse invalide"))
            erreurs += 1
            print(f"[nok]  {destinataire['email']} : adresse invalide")

        except smtplib.SMTPAuthenticationError:
            print(f"[STOP] {compte['adresse']} : mot de passe refuse.")
            melange = [c for c in melange if c["cle"] != compte["cle"]]
            erreurs += 1

        except Exception as e:
            cx.execute("UPDATE destinataires SET etat='echec', erreur=? WHERE email=?",
                       (str(e)[:300], destinataire["email"]))
            erreurs += 1
            print(f"[nok]  {destinataire['email']} : {e}")

        cx.commit()
        if i < len(lignes) - 1:
            attente = max(30, pause_minutes * 60 + random.randint(-60, 60))
            time.sleep(attente)

    return envoyes, erreurs


def envoyer_test_reel(cx, adresse, cle_compte=None):
    """
    Envoie un seul message, avec la personnalisation et la signature reelles,
    a l'adresse indiquee. Le lead servant de modele n'est pas marque comme
    envoye : il reste disponible pour la vraie campagne.
    """
    from envoi import composer

    prets, _ = comptes_configures()
    if cle_compte:
        prets = [c for c in prets if c["cle"] == cle_compte.lower()]
    if not prets:
        print("Aucun compte expediteur disponible.")
        return
    compte = prets[0]

    modele = cx.execute("""
        SELECT * FROM destinataires WHERE etat = 'a_envoyer' ORDER BY ajoute_le LIMIT 1
    """).fetchone()
    if not modele:
        print("Aucun lead en base pour servir de modele.")
        return

    objet, corps, html = construire(dict(modele), compte)
    message = composer(compte, {"email": adresse, "nom": ""}, f"[TEST] {objet}", corps, html)

    print(f"Modele : {modele['email']} ({modele['cabinet']})")
    print(f"Objet  : [TEST] {objet}")
    try:
        with se_connecter(compte) as serveur:
            serveur.send_message(message)
        print(f"[ok]   envoye depuis {compte['adresse']} vers {adresse}")
    except Exception as e:
        print(f"[nok]  {compte['adresse']} : {e}")


NOM_TACHE = "LumenJuris - Prospection 8h30"


def etat_tache_windows():
    """Interroge le Planificateur de taches pour savoir ou en est la routine."""
    infos = {}
    try:
        resultat = subprocess.run(
            ["schtasks", "/Query", "/TN", NOM_TACHE, "/FO", "LIST", "/V"],
            capture_output=True, text=True, encoding="cp850", errors="replace",
        )
        if resultat.returncode != 0:
            return {"Tache planifiee": "ABSENTE - la routine ne se lancera pas"}
        interessantes = ("Prochaine ex", "Dernière ex", "Derniere ex",
                         "Dernier résultat", "Dernier resultat", "État", "Etat")
        for ligne in (resultat.stdout or "").splitlines():
            if ":" not in ligne:
                continue
            cle, valeur = ligne.split(":", 1)
            cle, valeur = cle.strip(), valeur.strip()
            if any(cle.startswith(motif) for motif in interessantes) and valeur:
                infos[cle] = valeur
    except Exception as e:
        infos["Erreur de lecture"] = str(e)[:120]
    return infos


def synchroniser_routine(cx, config, derniere_execution=None):
    """Remplit l'onglet Routine : la tache Windows, vue depuis le Sheet."""
    q = quotas()
    lignes = [["Tache planifiee", NOM_TACHE]]
    for cle, valeur in etat_tache_windows().items():
        lignes.append([cle, valeur])
    lignes.append(["", ""])
    lignes.append(["ACTIF", config.get("ACTIF", "oui")])
    lignes.append(["Emails par boite et par jour", config.get("MAX_PAR_BOITE")])
    lignes.append(["Emails maximum par site", config.get("MAX_PAR_DOMAINE")])
    lignes.append(["Minutes entre deux envois", config.get("PAUSE_MINUTES")])
    lignes.append(["Stock cible", config.get("STOCK_CIBLE")])
    lignes.append(["", ""])
    lignes.append(["Stock disponible", base.stock_disponible(cx)])
    lignes.append(["SerpApi ce mois", f"{q['serpapi']}/{PLAFOND_SERPAPI}"])
    lignes.append(["Scrape.do ce mois", f"{q['scrapedo']}/{PLAFOND_SCRAPEDO}"])
    lignes.append(["Recherches restantes", q["restant"]])
    lignes.append(["Combinaisons utilisees",
                   f"{len(base.requetes_deja_faites(cx))}/{generateur.total_disponible()}"])
    if derniere_execution:
        lignes.append(["", ""])
        lignes.append(["Derniere execution vue par le script", derniere_execution])
    lignes.append(["", ""])
    lignes.append(["Pour arreter", "Mettre ACTIF sur non dans l'onglet Config"])
    try:
        sheets.remplacer_routine(lignes)
        print("[sheet] onglet Routine mis a jour.")
    except Exception as e:
        print(f"[sheet] onglet Routine non ecrit ({e})")


def synchroniser_sheet(cx):
    try:
        lignes = [
            [
                l["email"], l["cabinet"] or "", l["specialite"] or "",
                l["type_email"] or "", l["site"] or "", l["domaine"] or "",
                l["etat"] or "", l["compte"] or "", l["envoye_le"] or "",
                l["sujet"] or "", l["erreur"] or "",
            ]
            for l in cx.execute("SELECT * FROM destinataires ORDER BY ajoute_le DESC")
        ]
        n = sheets.remplacer_leads(lignes)
        print(f"[sheet] {n} lead(s) synchronise(s).")
        return True
    except Exception as e:
        print(f"[sheet] synchronisation impossible ({e}). La base locale reste a jour.")
        return False


def afficher_etat(cx):
    print("\nEtat de la base")
    print("-" * 46)
    for ligne in cx.execute(
        "SELECT etat, COUNT(*) n FROM destinataires GROUP BY etat ORDER BY n DESC"
    ):
        print(f"  {ligne['etat']:<14} {ligne['n']}")

    q = quotas()
    faites = len(base.requetes_deja_faites(cx))
    print(f"\nSerpApi ce mois      {q['serpapi']}/{PLAFOND_SERPAPI}")
    print(f"Scrape.do ce mois    {q['scrapedo']}/{PLAFOND_SCRAPEDO}  (secours automatique)")
    print(f"Recherches restantes {q['restant']}")
    print(f"Combinaisons faites  {faites}/{generateur.total_disponible()}")
    print(f"Stock disponible     {base.stock_disponible(cx)}")

    print("\nEnvois des 24 dernieres heures")
    print("-" * 46)
    for compte in COMPTES:
        restant = base.quota_restant(cx, compte["cle"], 20)
        etat = "pret" if mot_de_passe(compte) else "PAS DE MOT DE PASSE"
        print(f"  {compte['adresse']:<28} {20 - restant}/20  ({etat})")
    print()


def verifier():
    """
    Controle complet avant le premier lancement : secrets, acces au Sheet,
    memoire des leads. N'envoie aucun email et n'ecrit rien.
    """
    ok = True
    print("=== Verification de la configuration ===\n")

    print("1. Comptes expediteurs")
    prets, manquants = comptes_configures()
    for compte in prets:
        print(f"   [ok]      {compte['adresse']}")
    for compte in manquants:
        print(f"   [ABSENT]  {compte['adresse']} : pas de mot de passe")
    if not prets:
        print("   -> aucun compte utilisable, aucun email ne pourrait partir.")
        ok = False

    print("\n2. Connexion au serveur d'envoi")
    for compte in prets:
        try:
            with se_connecter(compte):
                print(f"   [ok]      {compte['adresse']} : identifiants acceptes")
        except Exception as e:
            print(f"   [ECHEC]   {compte['adresse']} : {str(e)[:120]}")
            ok = False

    print("\n3. Google Sheets")
    try:
        config = sheets.lire_config()
        print(f"   [ok]      configuration lue : ACTIF={config['ACTIF']}, "
              f"{config['MAX_PAR_BOITE']} emails par boite, "
              f"{config['MAX_PAR_DOMAINE']} maximum par site")
        leads = sheets.lire_leads()
        envoyes = sum(1 for l in leads if l.get("etat") == "envoye")
        print(f"   [ok]      {len(leads)} lead(s) dans l'onglet Leads, "
              f"dont {envoyes} deja contacte(s)")
        if not leads:
            print("   -> onglet Leads vide : la memoire anti-doublon serait perdue.")
            ok = False
    except Exception as e:
        print(f"   [ECHEC]   {str(e)[:200]}")
        ok = False

    print("\n4. Recherche de nouveaux prospects")
    for nom, variable in (("SerpApi", "SERPAPI_API_KEY"), ("Scrape.do", "SCRAPEDO_API_KEY")):
        import os
        presente = bool(os.environ.get(variable)) or (SCRAPING / ".env").exists()
        print(f"   [{'ok' if presente else 'ABSENT'}]      {nom}")
    q = quotas()
    print(f"             SerpApi {q['serpapi']}/{PLAFOND_SERPAPI}, "
          f"Scrape.do {q['scrapedo']}/{PLAFOND_SCRAPEDO}")

    print("\n" + ("=== TOUT EST PRET ===" if ok else "=== CONFIGURATION INCOMPLETE ==="))
    if ok:
        print("Aucun email n'a ete envoye. Lancez `python routine.py` pour demarrer.")
    return ok


def main():
    p = argparse.ArgumentParser(description="Routine quotidienne de prospection.")
    p.add_argument("--verifier", action="store_true",
                   help="controle la configuration sans rien envoyer")
    p.add_argument("--etat", action="store_true", help="affiche l'etat sans rien envoyer")
    p.add_argument("--recolte", action="store_true", help="constitue le stock seulement")
    p.add_argument("--envoi", action="store_true", help="envoie seulement")
    p.add_argument("--simule", action="store_true", help="affiche les messages sans envoyer")
    p.add_argument("--sans-sheet", action="store_true", help="ignore Google Sheets")
    p.add_argument("--test-vers", type=str, default=None,
                   help="envoie un seul message reel, personnalise, a cette adresse")
    p.add_argument("--compte", type=str, default=None,
                   help="expediteur a utiliser pour le test : geoffrey ou lumen")
    a = p.parse_args()

    if a.verifier:
        sys.exit(0 if verifier() else 1)

    cx = base.ouvrir()

    if a.test_vers:
        envoyer_test_reel(cx, a.test_vers, a.compte)
        return

    if a.etat:
        afficher_etat(cx)
        return

    if a.sans_sheet:
        config = {"ACTIF": "oui", "MAX_PAR_BOITE": 20, "MAX_PAR_DOMAINE": 3,
                  "PAUSE_MINUTES": 5, "STOCK_CIBLE": 40}
    else:
        config = sheets.lire_config()

    if config["ACTIF"] != "oui" and not a.simule:
        print(f"ACTIF = {config['ACTIF']} dans le Sheet. Routine arretee.")
        base.ajouter_journal(cx, "arret", "ACTIF different de oui")
        return

    # En ligne, la base SQLite repart vide a chaque execution : on la reconstruit
    # depuis le Sheet, sinon les destinataires deja contactes le seraient a nouveau.
    if base.est_vide(cx) and not a.sans_sheet:
        try:
            restaures = base.restaurer_depuis_sheet(cx, sheets.lire_leads())
            print(f"Base vide : {restaures} lead(s) restaure(s) depuis le Sheet.")
        except Exception as e:
            print(f"[STOP] base vide et Sheet illisible ({e}). "
                  f"Arret pour ne pas risquer de recontacter des adresses.")
            return

    debut = datetime.now()
    print(f"=== Routine du {debut:%d/%m/%Y %H:%M} ===")
    recoltes, recherches = 0, 0
    envoyes, erreurs = 0, 0

    if not a.envoi:
        try:
            recoltes, recherches = recolter(cx, config["STOCK_CIBLE"])
        except Exception as e:
            erreurs += 1
            print(f"[erreur] recolte : {e}")
            base.ajouter_journal(cx, "recolte", str(e)[:300], erreurs=1)

    if not a.recolte:
        envoyes, erreurs_envoi = envoyer(
            cx, config["MAX_PAR_BOITE"], config["PAUSE_MINUTES"],
            config["MAX_PAR_DOMAINE"], simulation=a.simule
        )
        erreurs += erreurs_envoi

    utilise, plafond = quota_serpapi()
    detail = f"{recherches} recherche(s), stock {base.stock_disponible(cx)}"
    base.ajouter_journal(cx, "routine", detail, recoltes, envoyes, utilise, erreurs)

    if not a.sans_sheet and not a.simule:
        synchroniser_sheet(cx)
        try:
            sheets.ajouter_journal([
                debut.strftime("%Y-%m-%d %H:%M"), "resume", "", "", "", "",
                f"{envoyes} envoye(s)",
                f"{detail} | {recoltes} lead(s) recolte(s) | "
                f"SerpApi {utilise}/{plafond} | {erreurs} erreur(s)",
            ])
        except Exception as e:
            print(f"[sheet] resume non ecrit ({e})")
        synchroniser_routine(cx, config, debut.strftime("%d/%m/%Y %H:%M"))

    duree = (datetime.now() - debut).total_seconds() / 60
    print(f"\n=== Termine en {duree:.0f} min ===")
    print(f"Leads recoltes : {recoltes} | Emails envoyes : {envoyes} | Erreurs : {erreurs}")
    print(f"SerpApi : {utilise}/{plafond} | Stock restant : {base.stock_disponible(cx)}")
    if not a.sans_sheet:
        print(f"Sheet : {sheets.lien()}")
    cx.close()


if __name__ == "__main__":
    main()
