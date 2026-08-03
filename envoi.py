"""
Envoi de mails en rotation sur plusieurs expediteurs.

Usage :
    python envoi.py --test              -> 1 mail de test vers ta propre adresse
    python envoi.py --nombre 15         -> envoie 15 mails de la liste, 1 toutes les 5 min
    python envoi.py --etat              -> ou en est-on

Les mots de passe sont lus dans les variables d'environnement
(SMTP_PASS_GEOFFREY, SMTP_PASS_EDOUARD, SMTP_PASS_LUMEN) : rien n'est
stocke dans ce fichier.
"""

import os
import ssl
import csv
import sys
import time
import random
import smtplib
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

DOSSIER = Path(__file__).parent
BASE = DOSSIER / "envois.db"
LISTE = DOSSIER / "liste.csv"
MESSAGE = DOSSIER / "message.txt"
MDP = DOSSIER / "mdp.txt"

ADRESSE_TEST = "geoffreypin@gmail.com"

COMPTES = [
    {
        "cle": "geoffrey",
        "serveur": "smtp.gmail.com",
        "port": 587,
        "adresse": "geoffreypin@gmail.com",
        "nom": "Geoffrey Pin",
        "plafond_jour": 30,
        "jeton": "geoffrey",
    },
    {
        "cle": "lumen",
        "serveur": "mail.lumenjuris.com",
        "port": 465,
        "adresse": "contact@lumenjuris.com",
        # Un nom de personne : « LumenJuris <contact@lumenjuris.com> » donnait
        # « Je suis LumenJuris, de Lumen Juris » dans le corps du message.
        "nom": "Geoffrey Pin",
        "plafond_jour": 30,
        # Cette adresse n'est pas un compte Google : elle part par l'API Gmail
        # sous le jeton de geoffrey, ou elle est declaree comme adresse d'envoi
        # verifiee. Verifie le 03/08/2026 : Gmail ne reecrit pas l'expediteur.
        "jeton": "geoffrey",
    },
    {
        "cle": "edouard",
        "serveur": "smtp.gmail.com",
        "port": 587,
        "adresse": "edouardlopro@gmail.com",
        "nom": "Edouard Lopro",
        "plafond_jour": 30,
        "jeton": "edouard",
    },
]


# --------------------------------------------------------------------------
# base de donnees : sert a ne jamais envoyer deux fois au meme destinataire
# --------------------------------------------------------------------------

def ouvrir_base():
    cx = sqlite3.connect(BASE)
    cx.row_factory = sqlite3.Row
    cx.execute("""
        CREATE TABLE IF NOT EXISTS destinataires (
            email    TEXT PRIMARY KEY,
            nom      TEXT,
            etat     TEXT DEFAULT 'a_envoyer',
            compte   TEXT,
            envoye_le TEXT,
            erreur   TEXT
        )""")
    cx.execute("""
        CREATE TABLE IF NOT EXISTS exclusions (
            email  TEXT PRIMARY KEY,
            motif  TEXT
        )""")
    cx.commit()
    return cx


def importer_liste(cx):
    """Charge liste.csv dans la base. Les doublons sont ignores."""
    if not LISTE.exists():
        return 0
    ajoutes = 0
    with LISTE.open(encoding="utf-8-sig", newline="") as f:
        # accepte un CSV avec en-tete (email, nom) ou une simple liste brute
        contenu = f.read()
    lignes = [l.strip() for l in contenu.splitlines() if l.strip()]
    if not lignes:
        return 0
    separateur = ";" if lignes[0].count(";") > lignes[0].count(",") else ","
    entete = "email" in lignes[0].lower()
    depart = 1 if entete else 0
    for ligne in lignes[depart:]:
        champs = [c.strip().strip('"') for c in ligne.split(separateur)]
        email = champs[0].lower()
        if "@" not in email:
            continue
        nom = champs[1] if len(champs) > 1 else ""
        cur = cx.execute(
            "INSERT OR IGNORE INTO destinataires (email, nom) VALUES (?, ?)",
            (email, nom),
        )
        ajoutes += cur.rowcount
    cx.commit()
    return ajoutes


def quota_restant(cx, compte):
    depuis = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    (n,) = cx.execute(
        "SELECT COUNT(*) FROM destinataires WHERE compte = ? AND envoye_le > ?",
        (compte["cle"], depuis),
    ).fetchone()
    return compte["plafond_jour"] - n


# --------------------------------------------------------------------------
# envoi
# --------------------------------------------------------------------------

def lire_mdp_fichier():
    """
    Lit mdp.txt. Chaque ligne du type

        mot de passe geoffreypin@gmail : xxxx xxxx xxxx xxxx

    est associee au compte dont l'adresse apparait a gauche des deux points.
    Les autres lignes (ports, serveurs, commentaires) sont ignorees.
    """
    trouves = {}
    if not MDP.exists():
        return trouves
    for ligne in MDP.read_text(encoding="utf-8", errors="replace").splitlines():
        if "@" not in ligne or ":" not in ligne:
            continue
        gauche, droite = ligne.split(":", 1)
        valeur = droite.strip()
        if not valeur:
            continue
        for compte in COMPTES:
            identifiant = compte["adresse"].split("@")[0].lower()
            if identifiant in gauche.lower():
                # les mots de passe d'application Gmail sont affiches par
                # groupes de 4 : on retire les espaces
                if "gmail" in compte["serveur"]:
                    valeur = "".join(valeur.split())
                trouves[compte["cle"]] = valeur
    return trouves


_MDP_FICHIER = None


def mot_de_passe(compte):
    """Variable d'environnement en priorite, sinon mdp.txt."""
    global _MDP_FICHIER
    depuis_env = os.environ.get(f"SMTP_PASS_{compte['cle'].upper()}")
    if depuis_env:
        return depuis_env
    if _MDP_FICHIER is None:
        _MDP_FICHIER = lire_mdp_fichier()
    return _MDP_FICHIER.get(compte["cle"])


def jeton_api(compte):
    """Cle d'autorisation Gmail utilisable par ce compte, ou None."""
    cle = compte.get("jeton")
    if not cle:
        return None
    try:
        import envoi_gmail
        envoi_gmail.charger_identifiants(cle)
        return cle
    except Exception:
        return None


def voie(compte):
    """Chemin d'envoi qui sera reellement emprunte : 'api', 'smtp' ou None."""
    if jeton_api(compte):
        return "api"
    return "smtp" if mot_de_passe(compte) else None


def comptes_configures():
    prets, manquants = [], []
    for c in COMPTES:
        (prets if voie(c) else manquants).append(c)
    return prets, manquants


def expedier(compte, message):
    """
    Envoie un message deja compose. Renvoie le chemin emprunte, pour le journal.

    L'API Gmail passe en premier : c'est le seul chemin qui fonctionne depuis
    l'environnement en ligne, ou les ports SMTP sont bloques. Le repli SMTP ne
    sert qu'en local, si l'autorisation Google manque ou a expire.
    """
    cle = jeton_api(compte)
    if cle:
        import envoi_gmail
        try:
            return f"api:{envoi_gmail.envoyer_message(cle, message)}"
        except Exception as e:
            if not mot_de_passe(compte):
                raise
            print(f"[api] {compte['adresse']} : {str(e)[:150]}")
            print("[api] repli sur SMTP.")
    with se_connecter(compte) as serveur:
        serveur.send_message(message)
    return "smtp"


def se_connecter(compte):
    contexte = ssl.create_default_context()
    if compte["port"] == 465:
        serveur = smtplib.SMTP_SSL(compte["serveur"], 465, context=contexte, timeout=30)
    else:
        serveur = smtplib.SMTP(compte["serveur"], compte["port"], timeout=30)
        serveur.starttls(context=contexte)
    serveur.login(compte["adresse"], mot_de_passe(compte))
    return serveur


def lire_message():
    """message.txt : 1re ligne = objet, ligne vide, puis le corps."""
    if not MESSAGE.exists():
        sys.exit(f"Fichier manquant : {MESSAGE}")
    texte = MESSAGE.read_text(encoding="utf-8").strip()
    if "\n" not in texte:
        sys.exit("message.txt doit contenir un objet, une ligne vide, puis le texte.")
    objet, corps = texte.split("\n", 1)
    return objet.strip(), corps.strip()


def composer(compte, destinataire, objet, corps, corps_html=None):
    nom = destinataire["nom"] or ""
    salutation = f"Bonjour {nom}".strip() if nom else "Bonjour"
    corps = corps.replace("{nom}", nom).replace("{bonjour}", salutation)
    objet = objet.replace("{nom}", nom)

    msg = EmailMessage()
    msg["From"] = f"{compte['nom']} <{compte['adresse']}>"
    msg["To"] = destinataire["email"]
    msg["Subject"] = objet
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=compte["adresse"].split("@")[1])
    msg["Reply-To"] = compte["adresse"]
    msg["List-Unsubscribe"] = "<mailto:contact@lumenjuris.com?subject=DESINSCRIPTION>"
    # La mention visible de desinscription a ete retiree a la demande.
    # L'en-tete List-Unsubscribe ci-dessus reste en place : c'est lui que Gmail
    # et Outlook utilisent pour afficher leur propre bouton « Se desabonner »,
    # et sa presence ameliore la delivrabilite.
    msg.set_content(corps)
    if corps_html:
        msg.add_alternative(corps_html, subtype="html")
    return msg


def envoyer_lot(nombre, pause, variation, cle_compte=None):
    cx = ouvrir_base()
    nouveaux = importer_liste(cx)
    if nouveaux:
        print(f"{nouveaux} nouvelle(s) adresse(s) importee(s) depuis liste.csv")

    prets, manquants = comptes_configures()
    for c in manquants:
        print(f"[ignore] {c['adresse']} : pas de mot de passe dans mdp.txt")
    prets = filtrer_comptes(prets, cle_compte)
    if not prets:
        sys.exit("Aucun compte configure. Renseigne au moins une variable SMTP_PASS_*.")

    actifs = [c for c in prets if quota_restant(cx, c) > 0]
    if not actifs:
        sys.exit("Plafond des 24 dernieres heures atteint sur tous les comptes.")

    objet, corps = lire_message()
    lignes = cx.execute("""
        SELECT * FROM destinataires
        WHERE etat = 'a_envoyer'
          AND email NOT IN (SELECT email FROM exclusions)
        LIMIT ?""", (nombre,)).fetchall()

    if not lignes:
        print("Rien a envoyer.")
        return

    print(f"{len(lignes)} mail(s) a envoyer, un toutes les ~{pause // 60} min.\n")
    envoyes = 0

    for i, destinataire in enumerate(lignes):
        if not actifs:
            print("Plus aucun compte disponible, arret.")
            break
        compte = actifs[i % len(actifs)]
        if quota_restant(cx, compte) <= 0:
            actifs.remove(compte)
            continue

        try:
            with se_connecter(compte) as serveur:
                serveur.send_message(composer(compte, destinataire, objet, corps))
            cx.execute(
                "UPDATE destinataires SET etat='envoye', compte=?, envoye_le=? "
                "WHERE email=?",
                (compte["cle"], datetime.now(timezone.utc).isoformat(),
                 destinataire["email"]),
            )
            envoyes += 1
            print(f"[ok]   {destinataire['email']}  <- {compte['adresse']}")

        except smtplib.SMTPRecipientsRefused as e:
            cx.execute("UPDATE destinataires SET etat='invalide', erreur=? WHERE email=?",
                       (str(e)[:300], destinataire["email"]))
            cx.execute("INSERT OR IGNORE INTO exclusions VALUES (?, ?)",
                       (destinataire["email"], "adresse invalide"))
            print(f"[nok]  {destinataire['email']} : adresse invalide")

        except smtplib.SMTPAuthenticationError:
            print(f"[STOP] {compte['adresse']} : mot de passe refuse. "
                  "Regenere le mot de passe d'application.")
            actifs.remove(compte)
            continue

        except smtplib.SMTPResponseException as e:
            if e.smtp_code in (421, 450, 451, 452, 550, 552):
                print(f"[pause] {compte['adresse']} : bride par le serveur "
                      f"(code {e.smtp_code}). Compte mis de cote.")
                actifs.remove(compte)
                continue
            cx.execute("UPDATE destinataires SET etat='echec', erreur=? WHERE email=?",
                       (str(e)[:300], destinataire["email"]))
            print(f"[nok]  {destinataire['email']} : {e}")

        except Exception as e:  # reseau, DNS, TLS...
            cx.execute("UPDATE destinataires SET etat='echec', erreur=? WHERE email=?",
                       (str(e)[:300], destinataire["email"]))
            print(f"[nok]  {destinataire['email']} : {e}")

        cx.commit()

        if i < len(lignes) - 1 and actifs:
            attente = max(30, pause + random.randint(-variation, variation))
            time.sleep(attente)

    cx.commit()
    cx.close()
    print(f"\nTermine : {envoyes} mail(s) envoye(s).")


def filtrer_comptes(comptes, cle):
    """--compte lumen : restreint l'envoi a un seul expediteur."""
    if not cle:
        return comptes
    choix = [c for c in comptes if c["cle"] == cle.lower()]
    if not choix:
        connus = ", ".join(c["cle"] for c in COMPTES)
        sys.exit(f"Compte inconnu : {cle}. Valeurs possibles : {connus}")
    return choix


def envoyer_test(cle_compte=None, destinataire=None, nom=None):
    prets, manquants = comptes_configures()
    for c in manquants:
        print(f"[ignore] {c['adresse']} : pas de mot de passe dans mdp.txt")
    prets = filtrer_comptes(prets, cle_compte)
    if not prets:
        sys.exit("Aucun compte configure (ou le compte demande n'a pas de mot de passe).")

    cible = (destinataire or ADRESSE_TEST).strip().lower()
    if "@" not in cible:
        sys.exit(f"Adresse de test invalide : {cible}")

    objet, corps = lire_message()
    faux = {"email": cible, "nom": nom or ""}

    for compte in prets:
        try:
            msg = composer(compte, faux, "[TEST] " + objet, corps)
            with se_connecter(compte) as serveur:
                serveur.send_message(msg)
            print(f"[ok]   test envoye depuis {compte['adresse']} vers {cible}")
        except Exception as e:
            print(f"[nok]  {compte['adresse']} : {e}")


def afficher_etat():
    cx = ouvrir_base()
    importer_liste(cx)
    print("\nEtat de la liste")
    print("-" * 40)
    for ligne in cx.execute(
        "SELECT etat, COUNT(*) n FROM destinataires GROUP BY etat ORDER BY n DESC"
    ):
        print(f"  {ligne['etat']:<12} {ligne['n']}")
    print("\nEnvois des dernieres 24 h")
    print("-" * 40)
    for compte in COMPTES:
        restant = quota_restant(cx, compte)
        utilise = compte["plafond_jour"] - restant
        etat = "mot de passe OK" if mot_de_passe(compte) else "PAS DE MOT DE PASSE"
        print(f"  {compte['adresse']:<28} {utilise}/{compte['plafond_jour']}  ({etat})")
    print()
    cx.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Envoi de mails en rotation.")
    p.add_argument("--test", action="store_true",
                   help="envoie un mail de test vers ta propre adresse")
    p.add_argument("--etat", action="store_true", help="affiche l'avancement")
    p.add_argument("--nombre", type=int, default=15,
                   help="nombre de mails a envoyer (defaut 15)")
    p.add_argument("--pause", type=int, default=300,
                   help="secondes entre deux envois (defaut 300 = 5 min)")
    p.add_argument("--variation", type=int, default=90,
                   help="variation aleatoire de la pause, en secondes")
    p.add_argument("--compte", type=str, default=None,
                   help="n'utiliser qu'un seul expediteur : geoffrey, lumen ou edouard")
    p.add_argument("--vers", type=str, default=None,
                   help=f"destinataire du test (defaut {ADRESSE_TEST})")
    p.add_argument("--nom", type=str, default=None,
                   help="nom utilise dans {nom} et {bonjour} pour le test")
    a = p.parse_args()

    if a.test:
        envoyer_test(a.compte, a.vers, a.nom)
    elif a.etat:
        afficher_etat()
    else:
        envoyer_lot(a.nombre, a.pause, a.variation, a.compte)
