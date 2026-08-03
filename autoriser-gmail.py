"""
Autorise une adresse Gmail a envoyer des emails via l'API web de Google.

A lancer UNE SEULE FOIS par adresse, sur votre ordinateur. Le navigateur
s'ouvre, vous cliquez « Autoriser », et le script ecrit un jeton reutilisable.
Ce jeton remplace le mot de passe : il permet d'envoyer sans passer par SMTP,
qui est bloque dans l'environnement en ligne.

    python autoriser-gmail.py geoffrey
    python autoriser-gmail.py edouard

Prerequis : le fichier client_secret.json telecharge depuis Google Cloud,
place dans ce dossier. La marche a suivre est dans GMAIL-API.md.
"""

import json
import sys
from pathlib import Path

DOSSIER = Path(__file__).parent
CLIENT = DOSSIER / "client_secret.json"

# La permission la plus etroite possible : envoyer, rien d'autre. Ce jeton ne
# permet ni de lire vos emails, ni de les supprimer.
PORTEE = ["https://www.googleapis.com/auth/gmail.send"]


def fichier_jeton(cle):
    return DOSSIER / f"gmail-{cle}.json"


def autoriser(cle):
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not CLIENT.exists():
        sys.exit(
            f"Fichier manquant : {CLIENT}\n\n"
            "Telechargez-le depuis Google Cloud Console (identifiant OAuth de\n"
            "type « Application de bureau »), renommez-le client_secret.json,\n"
            "et placez-le dans ce dossier. Voir GMAIL-API.md."
        )

    print(f"\nAutorisation de l'adresse « {cle} ».")
    print("Votre navigateur va s'ouvrir. Connectez-vous avec l'adresse voulue,")
    print("puis cliquez « Autoriser ».\n")

    flux = InstalledAppFlow.from_client_secrets_file(str(CLIENT), PORTEE)
    # access_type=offline + prompt=consent : indispensables pour obtenir un
    # jeton de rafraichissement. Sans eux Google n'en renvoie pas a la
    # deuxieme autorisation, et le jeton expire au bout d'une heure.
    identifiants = flux.run_local_server(
        port=0, access_type="offline", prompt="consent"
    )

    if not identifiants.refresh_token:
        sys.exit(
            "Google n'a pas renvoye de jeton de rafraichissement.\n"
            "Retirez l'acces sur https://myaccount.google.com/permissions "
            "puis relancez."
        )

    cible = fichier_jeton(cle)
    cible.write_text(
        json.dumps(
            {
                "client_id": identifiants.client_id,
                "client_secret": identifiants.client_secret,
                "refresh_token": identifiants.refresh_token,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n[ok] Jeton enregistre dans {cible.name}")
    print("     Ce fichier est exclu du depot : il ne partira jamais sur GitHub.")
    print("\nEtape suivante : verifiez que l'envoi fonctionne, avec")
    print(f"     python envoi_gmail.py --test {cle}")
    return cible


def main():
    if len(sys.argv) < 2:
        sys.exit(
            "Usage : python autoriser-gmail.py <cle>\n"
            "  <cle> est l'identifiant du compte : geoffrey, edouard ou lumen.\n"
            "  Exemple : python autoriser-gmail.py geoffrey"
        )
    autoriser(sys.argv[1].strip().lower())


if __name__ == "__main__":
    main()
