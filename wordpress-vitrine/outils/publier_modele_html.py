# -*- coding: utf-8 -*-
"""Publie une page modèle WordPress sans envoyer de Word, PDF ou image."""
import re
import sys
from pathlib import Path

import modeles_contrat as mc


def contenu_page(slug, etat):
    contenu = mc.page_modele(slug, etat, publics_seulement=True)
    # Aucun fichier n'est envoyé à WordPress : on retire le menu Télécharger.
    contenu = re.sub(r'<details class="lj-dl">.*?</details>', '', contenu, flags=re.S)
    return contenu


def publier(slug, en_ligne=True):
    f = mc.fiche(slug)
    article = mc.DOSSIER / slug / "article.html"
    modele = mc.DOSSIER / slug / "modele.txt"
    if not article.exists() or not modele.exists():
        sys.exit(f"Fichiers du modèle manquants pour {slug}.")
    if "<table" not in article.read_text(encoding="utf-8"):
        sys.exit("Refus : article.html doit contenir au moins un tableau (<table>).</")

    etat = mc.lire_etat()
    em = etat["modeles"].setdefault(slug, {})

    # La bibliothèque existe déjà : aucune reconstruction, aucun média envoyé.
    parent_id = etat.get("bibliotheque", {}).get("id")
    if not parent_id:
        pages = mc.api("wp/v2/pages?slug=modele-contrat&per_page=1&context=edit")
        if not pages:
            sys.exit("Bibliothèque modele-contrat introuvable.")
        parent_id = pages[0]["id"]
        etat.setdefault("bibliotheque", {})["id"] = parent_id

    statut = "publish" if en_ligne else em.get("statut", "draft")
    donnees = {
        "title": f["titre_h1"],
        "slug": slug,
        "parent": parent_id,
        "status": statut,
        "content": contenu_page(slug, etat),
    }
    p = mc.ecrire_page(em.get("id"), donnees, slug)
    em.update(id=p["id"], statut=p["status"], lien=p["link"])
    mc.ecrire_etat(etat)

    try:
        mc.meta_seo(p["id"], f["titre_seo"], f["meta_description"], f["mot_cle"], f["nom"])
    except Exception as err:
        print(f"  SEO Rank Math non bloquant : {err}")

    print(f"OK {slug} : page {p['id']} ({p['status']})")
    print(f"URL : {f['url']}")
    if en_ligne:
        mc.verifier(f["url"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit("Usage : python publier_modele_html.py <slug> [--brouillon]")
    publier(sys.argv[1], en_ligne="--brouillon" not in sys.argv[2:])
