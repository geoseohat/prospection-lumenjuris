"""
Miroir lisible de la base dans Google Sheets.

Trois onglets :
  Config   -> ACTIF oui/non, plafonds, pause. C'est votre bouton marche/arret.
  Leads    -> un lead par ligne, avec l'expediteur utilise et la date d'envoi.
  Journal  -> une ligne par execution : quotas, recoltes, envoyes, erreurs.

Le Sheet ne pilote rien de critique : si Google est indisponible, la routine
continue et resynchronise a la prochaine execution.
"""

import os
import sys
from pathlib import Path

from googleapiclient.discovery import build

DOSSIER = Path(__file__).parent
COMPTE_SERVICE = DOSSIER / "service-account.json"
CREDENTIALS = DOSSIER / "credentials.json"
JETON = DOSSIER / "token.json"

PORTEE = ["https://www.googleapis.com/auth/spreadsheets"]

# Le classeur que vous avez cree.
SHEET_ID = "1xkGhCdJTmYBpacLtFk8k8VOtEYUjBaFYiRvRA3xkb14"

ENTETES_LEADS = [
    "email", "cabinet", "specialite", "type_email", "site", "domaine",
    "etat", "expediteur", "date_envoi", "objet", "erreur",
]
# Le Journal recoit une ligne par email envoye, plus une ligne de resume par
# execution : on peut donc y suivre chaque envoi individuellement.
ENTETES_JOURNAL = [
    "date", "type", "email", "cabinet", "expediteur", "objet", "statut", "detail",
]
ENTETES_ROUTINE = ["information", "valeur"]
CONFIG_DEFAUT = [
    ["parametre", "valeur", "commentaire"],
    ["ACTIF", "oui", "Mettre non pour arreter la routine des demain"],
    ["MAX_PAR_BOITE", "20", "Nombre d'emails par adresse expeditrice et par jour"],
    ["MAX_PAR_DOMAINE", "3", "Nombre maximum d'emails par site internet, au total"],
    ["PAUSE_MIN", "1", "Attente minimum entre deux envois, en minutes"],
    ["PAUSE_MAX", "5", "Attente maximum entre deux envois, en minutes"],
    ["STOCK_CIBLE", "40", "Leads a constituer chaque matin avant d'envoyer"],
]


def adresse_compte_service():
    """Adresse a qui partager le Sheet. Renvoie None si le fichier est absent."""
    import json
    if not COMPTE_SERVICE.exists():
        return None
    try:
        return json.loads(COMPTE_SERVICE.read_text(encoding="utf-8")).get("client_email")
    except Exception:
        return None


def _service():
    from google.oauth2 import service_account

    # En ligne, le compte de service arrive par variable d'environnement :
    # aucun fichier sensible n'a besoin d'exister dans le depot.
    depuis_env = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if depuis_env:
        import json
        import base64
        # Le JSON contient des guillemets doubles, qui cassent le format .env.
        # On accepte donc aussi une valeur encodee en base64 : une seule ligne,
        # aucun caractere a echapper.
        if not depuis_env.lstrip().startswith("{"):
            depuis_env = base64.b64decode(depuis_env).decode("utf-8")
        identifiants = service_account.Credentials.from_service_account_info(
            json.loads(depuis_env), scopes=PORTEE
        )
        return build("sheets", "v4", credentials=identifiants).spreadsheets()

    # En local, le fichier suffit : ni expiration ni navigateur.
    if COMPTE_SERVICE.exists():
        identifiants = service_account.Credentials.from_service_account_file(
            str(COMPTE_SERVICE), scopes=PORTEE
        )
        return build("sheets", "v4", credentials=identifiants).spreadsheets()

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    identifiants = None
    if JETON.exists():
        identifiants = Credentials.from_authorized_user_file(str(JETON), PORTEE)
    if not identifiants or not identifiants.valid:
        if identifiants and identifiants.expired and identifiants.refresh_token:
            identifiants.refresh(Request())
        else:
            if not CREDENTIALS.exists():
                sys.exit(
                    f"Fichier manquant : {CREDENTIALS}\n"
                    "Telechargez-le depuis Google Cloud Console (identifiant OAuth "
                    "de type « Application de bureau »), puis relancez."
                )
            flux = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), PORTEE)
            identifiants = flux.run_local_server(port=0)
        JETON.write_text(identifiants.to_json(), encoding="utf-8")
    return build("sheets", "v4", credentials=identifiants).spreadsheets()


_SERVICE = None


def service():
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = _service()
    return _SERVICE


def onglets_existants(api):
    infos = api.get(spreadsheetId=SHEET_ID).execute()
    return {f["properties"]["title"] for f in infos.get("sheets", [])}


def preparer(api=None):
    """Cree les onglets manquants et pose les en-tetes. Idempotent."""
    api = api or service()
    presents = onglets_existants(api)
    demandes = []
    for titre in ("Routine", "Config", "Leads", "Journal"):
        if titre not in presents:
            demandes.append({"addSheet": {"properties": {"title": titre}}})
    if demandes:
        api.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": demandes}).execute()

    if "Config" not in presents:
        api.values().update(
            spreadsheetId=SHEET_ID, range="Config!A1",
            valueInputOption="RAW", body={"values": CONFIG_DEFAUT},
        ).execute()

    for titre, entetes in (("Leads", ENTETES_LEADS), ("Journal", ENTETES_JOURNAL),
                           ("Routine", ENTETES_ROUTINE)):
        actuel = api.values().get(spreadsheetId=SHEET_ID, range=f"{titre}!A1:Z1").execute()
        ligne = (actuel.get("values") or [[]])[0]
        # Reecrit l'en-tete s'il est absent ou s'il date d'une version anterieure.
        if ligne != entetes:
            api.values().update(
                spreadsheetId=SHEET_ID, range=f"{titre}!A1",
                valueInputOption="RAW", body={"values": [entetes]},
            ).execute()
    return api


def remplacer_routine(lignes):
    """Onglet Routine : etat de la tache planifiee, vu depuis le Sheet."""
    api = preparer()
    api.values().clear(spreadsheetId=SHEET_ID, range="Routine!A2:Z200").execute()
    if lignes:
        api.values().update(
            spreadsheetId=SHEET_ID, range="Routine!A2",
            valueInputOption="RAW", body={"values": lignes},
        ).execute()


def journal_envoi(date, email, cabinet, expediteur, objet, statut, detail=""):
    """Une ligne par email envoye. Silencieux en cas de panne reseau."""
    try:
        ajouter_journal([date, "envoi", email, cabinet, expediteur, objet, statut, detail])
        return True
    except Exception as e:
        print(f"[sheet] ligne journal non ecrite ({e})")
        return False


def lire_config():
    """Renvoie le contenu de l'onglet Config. Valeurs par defaut si injoignable."""
    defauts = {"ACTIF": "oui", "MAX_PAR_BOITE": 20, "MAX_PAR_DOMAINE": 3,
               "PAUSE_MIN": 1, "PAUSE_MAX": 5, "STOCK_CIBLE": 40}
    try:
        api = preparer()
        lignes = api.values().get(
            spreadsheetId=SHEET_ID, range="Config!A2:B50"
        ).execute().get("values", [])
    except Exception as e:
        print(f"[sheet] configuration illisible ({e}). Valeurs par defaut utilisees.")
        return defauts

    config = dict(defauts)
    for ligne in lignes:
        if len(ligne) < 2 or not ligne[0].strip():
            continue
        cle, valeur = ligne[0].strip().upper(), ligne[1].strip()
        if cle == "ACTIF":
            config["ACTIF"] = valeur.lower()
        elif cle in ("MAX_PAR_BOITE", "MAX_PAR_DOMAINE", "PAUSE_MIN", "PAUSE_MAX",
                     "STOCK_CIBLE"):
            try:
                config[cle] = int(valeur)
            except ValueError:
                pass
        # PAUSE_MINUTES, l'ancien reglage unique, est volontairement ignore :
        # il est remplace par PAUSE_MIN et PAUSE_MAX.

    # Une inversion des deux bornes ferait planter le tirage au sort.
    if config["PAUSE_MAX"] < config["PAUSE_MIN"]:
        config["PAUSE_MAX"] = config["PAUSE_MIN"]
    return config


def remplacer_leads(lignes):
    """Reecrit l'onglet Leads en entier : le Sheet reflete toujours la base."""
    api = preparer()
    api.values().clear(spreadsheetId=SHEET_ID, range="Leads!A2:Z100000").execute()
    if not lignes:
        return 0
    api.values().update(
        spreadsheetId=SHEET_ID, range="Leads!A2",
        valueInputOption="RAW", body={"values": lignes},
    ).execute()
    return len(lignes)


def lire_leads():
    """
    Relit l'onglet Leads. En execution en ligne, la base SQLite ne survit pas
    d'un jour a l'autre : c'est le Sheet qui porte la memoire, et donc
    l'anti-doublon. Renvoie une liste de dictionnaires.
    """
    api = preparer()
    valeurs = api.values().get(
        spreadsheetId=SHEET_ID, range="Leads!A2:Z100000"
    ).execute().get("values", [])
    leads = []
    for ligne in valeurs:
        if not ligne or not ligne[0].strip():
            continue
        complete = list(ligne) + [""] * (len(ENTETES_LEADS) - len(ligne))
        leads.append(dict(zip(ENTETES_LEADS, complete)))
    return leads


def ajouter_journal(ligne):
    api = preparer()
    api.values().append(
        spreadsheetId=SHEET_ID, range="Journal!A1",
        valueInputOption="RAW", insertDataOption="INSERT_ROWS",
        body={"values": [ligne]},
    ).execute()


def lien():
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
