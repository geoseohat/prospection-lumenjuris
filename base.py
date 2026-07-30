"""
Base SQLite : source de verite technique.

C'est elle qui garantit qu'une adresse n'est jamais recontactee, meme si le
reseau ou Google Sheets sont indisponibles. Le Sheet en est le miroir lisible.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

BASE = Path(__file__).parent / "envois.db"


def maintenant():
    return datetime.now(timezone.utc).isoformat()


def ouvrir():
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
    cx.execute("""
        CREATE TABLE IF NOT EXISTS requetes_faites (
            requete TEXT PRIMARY KEY,
            date    TEXT
        )""")
    cx.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT,
            etape       TEXT,
            detail      TEXT,
            recoltes    INTEGER DEFAULT 0,
            envoyes     INTEGER DEFAULT 0,
            serpapi     INTEGER DEFAULT 0,
            erreurs     INTEGER DEFAULT 0
        )""")

    # Colonnes ajoutees apres coup : la table existait deja sans elles.
    existantes = {c["name"] for c in cx.execute("PRAGMA table_info(destinataires)")}
    for colonne in ("cabinet", "specialite", "personnalisation", "source_url",
                    "site", "type_email", "domaine", "sujet", "ajoute_le",
                    "sheet_ligne"):
        if colonne not in existantes:
            cx.execute(f"ALTER TABLE destinataires ADD COLUMN {colonne} TEXT")
    cx.commit()
    return cx


def stock_disponible(cx):
    (n,) = cx.execute("""
        SELECT COUNT(*) FROM destinataires
        WHERE etat = 'a_envoyer'
          AND email NOT IN (SELECT email FROM exclusions)
    """).fetchone()
    return n


def requetes_deja_faites(cx):
    return {ligne["requete"] for ligne in cx.execute("SELECT requete FROM requetes_faites")}


def marquer_requete(cx, requete):
    cx.execute("INSERT OR IGNORE INTO requetes_faites VALUES (?, ?)", (requete, maintenant()))
    cx.commit()


def quota_restant(cx, cle_compte, plafond):
    depuis = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    (n,) = cx.execute(
        "SELECT COUNT(*) FROM destinataires WHERE compte = ? AND envoye_le > ?",
        (cle_compte, depuis),
    ).fetchone()
    return plafond - n


def ajouter_journal(cx, etape, detail, recoltes=0, envoyes=0, serpapi=0, erreurs=0):
    cx.execute(
        "INSERT INTO journal (date, etape, detail, recoltes, envoyes, serpapi, erreurs) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (maintenant(), etape, detail, recoltes, envoyes, serpapi, erreurs),
    )
    cx.commit()


def restaurer_depuis_sheet(cx, leads):
    """
    Recharge la base a partir de l'onglet Leads. Sert quand la base locale est
    absente : execution en ligne, nouveau poste, ou fichier supprime. L'etat
    'envoye' est preserve, donc personne n'est recontacte.
    """
    restaures = 0
    for lead in leads:
        email = (lead.get("email") or "").strip().lower()
        if "@" not in email:
            continue
        cur = cx.execute("""
            INSERT OR IGNORE INTO destinataires
                (email, cabinet, specialite, type_email, site, domaine,
                 etat, compte, envoye_le, sujet, erreur, ajoute_le)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                email,
                lead.get("cabinet", ""), lead.get("specialite", ""),
                lead.get("type_email", ""), lead.get("site", ""),
                lead.get("domaine", "") or email.split("@")[1],
                lead.get("etat") or "a_envoyer",
                lead.get("expediteur", ""), lead.get("date_envoi", ""),
                lead.get("objet", ""), lead.get("erreur", ""), maintenant(),
            ),
        )
        restaures += cur.rowcount
    cx.commit()
    return restaures


def est_vide(cx):
    (n,) = cx.execute("SELECT COUNT(*) FROM destinataires").fetchone()
    return n == 0


def importer_prospects(cx, lignes):
    """
    Insere les prospects extraits. La cle primaire sur l'email fait le travail
    d'anti-doublon : une adresse deja presente n'est jamais reinseree, donc
    jamais recontactee, quel que soit le nombre d'executions.
    """
    ajoutes = 0
    for p in lignes:
        email = (p.get("email") or "").strip().lower()
        if "@" not in email:
            continue
        prenom = (p.get("prenom") or "").strip()
        cur = cx.execute("""
            INSERT OR IGNORE INTO destinataires
                (email, nom, cabinet, specialite, personnalisation, source_url,
                 site, type_email, domaine, ajoute_le)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                email,
                prenom,
                (p.get("cabinet") or "").strip(),
                (p.get("specialites") or "").strip(),
                (p.get("personnalisation") or "").strip(),
                (p.get("source_personnalisation_url") or "").strip(),
                (p.get("site") or "").strip(),
                (p.get("type_email") or "").strip(),
                (p.get("id") or "").split("|")[0],
                maintenant(),
            ),
        )
        ajoutes += cur.rowcount
    cx.commit()
    return ajoutes
