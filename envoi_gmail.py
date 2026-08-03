"""
Envoi d'emails par l'API web de Gmail, sans SMTP.

Pourquoi : l'environnement d'execution en ligne bloque completement les ports
d'envoi de mail (587 et 465), y compris vers Google. Il ne laisse passer que
le trafic web classique. L'API Gmail passe par ce canal-la, donc elle marche
en ligne comme en local.

Ou sont les identifiants :
  - en local  : fichiers gmail-<cle>.json, produits par autoriser-gmail.py
  - en ligne  : variables d'environnement GMAIL_TOKEN_<CLE>, prioritaires,
                contenant le meme JSON (brut ou encode en base64)

Verification rapide :
    python envoi_gmail.py --test geoffrey
    python envoi_gmail.py --test geoffrey --vers autre@exemple.fr
"""

import os
import sys
import json
import base64
import argparse
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path
from email.message import EmailMessage

DOSSIER = Path(__file__).parent

JETON_URL = "https://oauth2.googleapis.com/token"
ENVOI_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

# Volontairement en urllib, et pas en requests : aucune dependance a installer,
# et urllib suit tout seul le proxy de l'environnement en ligne.


def charger_identifiants(cle):
    """
    Renvoie le trio client_id / client_secret / refresh_token pour une adresse.
    La variable d'environnement prime sur le fichier : en ligne il n'y a pas
    de fichier, en local il n'y a pas de variable.
    """
    depuis_env = os.environ.get(f"GMAIL_TOKEN_{cle.upper()}", "").strip()
    if depuis_env:
        # Le JSON contient des guillemets, qui cassent le format des variables
        # d'environnement. On accepte donc aussi une version encodee en base64,
        # sur une seule ligne, sans caractere a echapper. Meme principe que
        # GOOGLE_SERVICE_ACCOUNT_JSON dans sheets.py.
        if not depuis_env.lstrip().startswith("{"):
            depuis_env = base64.b64decode(depuis_env).decode("utf-8")
        return json.loads(depuis_env)

    fichier = DOSSIER / f"gmail-{cle}.json"
    if not fichier.exists():
        raise FileNotFoundError(
            f"Aucune autorisation pour « {cle} ».\n"
            f"Attendu : le fichier {fichier.name}, ou la variable "
            f"GMAIL_TOKEN_{cle.upper()}.\n"
            f"Pour la creer : python autoriser-gmail.py {cle}"
        )
    return json.loads(fichier.read_text(encoding="utf-8"))


def jeton_acces(identifiants):
    """
    Echange le jeton de rafraichissement (permanent) contre un jeton d'acces
    (valable une heure). C'est l'equivalent de la connexion au serveur SMTP.
    """
    donnees = urllib.parse.urlencode(
        {
            "client_id": identifiants["client_id"],
            "client_secret": identifiants["client_secret"],
            "refresh_token": identifiants["refresh_token"],
            "grant_type": "refresh_token",
        }
    ).encode()
    requete = urllib.request.Request(JETON_URL, data=donnees, method="POST")
    try:
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            return json.loads(reponse.read())["access_token"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(
            f"Autorisation refusee par Google ({e.code}). {detail}\n"
            "Le jeton a peut-etre ete revoque : relancez autoriser-gmail.py."
        ) from e


def envoyer_message(cle, message):
    """
    Envoie un objet EmailMessage deja compose. Renvoie l'identifiant attribue
    par Gmail, qui sert de preuve d'envoi.
    """
    acces = jeton_acces(charger_identifiants(cle))
    brut = base64.urlsafe_b64encode(message.as_bytes()).decode()
    requete = urllib.request.Request(
        ENVOI_URL,
        data=json.dumps({"raw": brut}).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {acces}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            return json.loads(reponse.read()).get("id", "")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"Envoi refuse par Gmail ({e.code}). {detail}") from e


def comptes_autorises(cles):
    """Parmi les cles proposees, celles qui ont une autorisation utilisable."""
    prets = []
    for cle in cles:
        try:
            charger_identifiants(cle)
            prets.append(cle)
        except Exception:
            pass
    return prets


def envoyer_test(cle, vers=None):
    from envoi import COMPTES

    compte = next((c for c in COMPTES if c["cle"] == cle), None)
    if compte is None:
        connus = ", ".join(c["cle"] for c in COMPTES)
        sys.exit(f"Compte inconnu : {cle}. Valeurs possibles : {connus}")

    cible = (vers or compte["adresse"]).strip()
    message = EmailMessage()
    message["From"] = f"{compte['nom']} <{compte['adresse']}>"
    message["To"] = cible
    message["Subject"] = "[TEST] Envoi par l'API Gmail"
    message.set_content(
        "Ce message a ete envoye par l'API web de Gmail, sans passer par SMTP.\n\n"
        "Si vous le lisez, le chemin d'envoi utilisable depuis l'environnement\n"
        "en ligne fonctionne, et la prospection peut y etre transferee.\n"
    )

    print(f"Envoi depuis {compte['adresse']} vers {cible} ...")
    identifiant = envoyer_message(cle, message)
    print(f"[ok] Message accepte par Gmail (identifiant {identifiant}).")
    print("     Verifiez la boite de reception du destinataire.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Envoi d'emails par l'API Gmail.")
    p.add_argument("--test", metavar="CLE",
                   help="envoie un message de test depuis ce compte")
    p.add_argument("--vers", default=None,
                   help="destinataire du test (defaut : le compte lui-meme)")
    a = p.parse_args()

    if not a.test:
        p.print_help()
        sys.exit(0)
    envoyer_test(a.test.strip().lower(), a.vers)
