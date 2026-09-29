# -*- coding: utf-8 -*-
"""Publie une page modèle WordPress sans envoyer de Word, PDF ou image."""
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

import modeles_contrat as mc


def contenu_page(slug, etat):
    contenu = mc.page_modele(slug, etat, publics_seulement=True)
    # Aucun fichier n'est envoyé à WordPress : on retire le menu Télécharger.
    return re.sub(r'<details class="lj-dl">.*?</details>', '', contenu, flags=re.S)


def post_json(chemin, donnees):
    """POST JSON en conservant le POST si o2switch renvoie une redirection 307/308."""
    url = f"{mc.SITE}/wp-json/{chemin}"
    corps = json.dumps(donnees).encode("utf-8")
    headers = {
        "Authorization": f"Basic {mc.wp_api.TOKEN}",
        "User-Agent": mc.wp_api.UA,
        "Content-Type": "application/json",
    }
    for _ in range(4):
        req = urllib.request.Request(url, data=corps, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code not in (307, 308):
                raise
            cible = err.headers.get("Location")
            if not cible:
                raise
            url = urllib.parse.urljoin(url, cible)
            print(f"  redirection WordPress {err.code} -> {url}")
    raise RuntimeError("Trop de redirections WordPress")


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
    parent_id = etat.get("bibliotheque", {}).get("id")
    if not parent_id:
        sys.exit("Bibliothèque modele-contrat absente de etat.json.")

    statut = "publish" if en_ligne else em.get("statut", "draft")
    donnees = {
        "title": f["titre_h1"],
        "slug": slug,
        "parent": parent_id,
        "status": statut,
        "content": contenu_page(slug, etat),
    }
    chemin = f"wp/v2/pages/{em['id']}" if em.get("id") else "wp/v2/pages"
    p = post_json(chemin, donnees)
    em.update(id=p["id"], statut=p["status"], lien=p["link"])
    mc.ecrire_etat(etat)

    try:
        meta = {
            "rank_math_title": f["titre_seo"],
            "rank_math_description": f["meta_description"],
            "rank_math_focus_keyword": f["mot_cle"],
            "rank_math_rich_snippet": "off",
            "rank_math_breadcrumb_title": f["nom"],
        }
        post_json("rankmath/v1/updateMeta", {"objectType": "post", "objectID": p["id"], "meta": meta})
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
