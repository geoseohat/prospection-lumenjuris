# -*- coding: utf-8 -*-
"""Priorite 8 : metadonnees SEO et partage social, via l'API Rank Math.

Plusieurs pages n'avaient pas de meta description propre : Rank Math reprenait
alors le premier texte de la page, ce qui donnait « Conforme RGPD ». On ecrit ici
des descriptions redigees, dans le vocabulaire retenu pour le positionnement.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wp_api  # noqa: E402

# page_id : (titre SEO ou None pour conserver, description)
META = {
    103: (
        "Analyse contractuelle assistée par IA — Logiciel juridique français",
        "Lumen Juris assiste les professionnels du droit dans l’analyse de leurs "
        "contrats : points de vigilance signalés, références juridiques françaises "
        "affichées, contrôle humain préservé. Hébergement en France."),
    2832: (
        None,
        "Où sont hébergées vos données, ce que nous faisons de vos documents, combien "
        "de temps nous les conservons et à qui nous les confions. Hébergement en "
        "France, sous-traitants et mesures de sécurité détaillés."),
    2909: (
        "FAQ — Confidentialité, sources juridiques et fiabilité",
        "Réponses précises sur la confidentialité de vos contrats, les sources "
        "juridiques interrogées, les limites de l’analyse par IA, la suppression de "
        "vos documents et le lieu d’hébergement des données."),
    2842: (
        None,
        "Préparez votre revue contractuelle : Lumen Juris signale les points de "
        "vigilance clause par clause, rattache chaque alerte à une référence "
        "juridique française et propose des reformulations à vérifier."),
    2630: (
        None,
        "Générez une trame de contrat adaptée à votre situation à partir d’un "
        "questionnaire, avec des variables réutilisables et des clauses rattachées "
        "aux textes officiels français, à relire avant signature."),
    2866: (
        None,
        "Suivez vos négociations contractuelles avec une trace exploitable à chaque "
        "étape : versions comparées, points de vigilance et références juridiques "
        "françaises pour préparer vos arbitrages."),
    2852: (
        None,
        "Ne manquez plus une échéance contractuelle : alertes calées sur les préavis "
        "réels extraits de vos clauses, portefeuille consolidé et piste d’audit."),
    2820: (
        None,
        "Signature électronique intégrée à votre flux contractuel, du contrat généré "
        "à la signature, avec les niveaux prévus par le règlement européen eIDAS."),
    607: (
        None,
        "Une juriste de métier et deux profils techniques, un outil d’assistance "
        "juridique appuyé sur les sources officielles françaises et développé avec "
        "les retours de professionnels du droit."),
    8: (None,
        "Éditeur, forme juridique, SIREN, siège, directeur de publication et "
        "hébergeur du site lumenjuris.com."),
    287: (None,
          "Responsable de traitement, bases légales, catégories de données, durées de "
          "conservation, hébergement en France et exercice de vos droits RGPD."),
}


def update_meta(post_id, rows):
    """rows : dict {cle_rank_math: valeur}."""
    payload = {"objectType": "post", "objectID": post_id, "meta": rows}
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{wp_api.SITE}/wp-json/rankmath/v1/updateMeta",
        data=body,
        headers={"Authorization": f"Basic {wp_api.TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": wp_api.UA},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")[:200]


def main():
    apply = "--apply" in sys.argv
    for post_id, (title, description) in META.items():
        rows = {"rank_math_description": description}
        if title:
            rows["rank_math_title"] = title
        print(f"{post_id:>5} : {description[:72]}...")
        if apply:
            print("       ", update_meta(post_id, rows))
    if not apply:
        print("\nMode simulation. Relancez avec --apply.")


if __name__ == "__main__":
    main()
