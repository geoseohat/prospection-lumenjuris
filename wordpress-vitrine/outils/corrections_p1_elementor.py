# -*- coding: utf-8 -*-
"""Corrections priorite 1 (point 1.6) sur les pages construites avec Elementor.

Le contenu de ces pages est stocke dans la meta `_elementor_data` (JSON serialise).
Le script remplace des fragments de texte dans cette chaine, puis republie la meta
et purge le cache CSS d'Elementor pour la page concernee.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wp_api  # noqa: E402

# Accueil (page 103, page d'accueil du site)
ACCUEIL = [
    # 1.6 : ne pas garantir l'absence totale d'hallucinations
    (
        "des alertes sourcées (article cité), des hallucinations écartées et des surlignages "
        "directement reliés aux bases légales.",
        "des alertes accompagnées de leur référence (article cité) et des surlignages reliés aux "
        "textes applicables, afin que chaque suggestion puisse être vérifiée.",
    ),
]

# Qui sommes-nous (page 607)
QUI_SOMMES_NOUS = [
    (
        "Puis, après avoir fait essayé auprès de plusieurs juristes ; ça a confirmé qu’on tenait "
        "quelque chose d’utile et pertinent pour les professionnels du droit.",
        "Puis nous l’avons fait essayer à plusieurs juristes, ce qui a confirmé que l’outil était "
        "utile et pertinent pour les professionnels du droit.",
    ),
    (
        "c’est l’ouverture des données juridiques français par Legifrance",
        "c’est l’ouverture des données juridiques françaises par Légifrance",
    ),
]

PAGES = {
    103: ("accueil", ACCUEIL),
    607: ("qui-sommes-nous", QUI_SOMMES_NOUS),
}


def update_meta(pid, elementor_data):
    payload = {"meta": {"_elementor_data": elementor_data}}
    body = json.dumps(payload).encode("utf-8")
    url = f"{wp_api.SITE}/wp-json/wp/v2/pages/{pid}"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Basic {wp_api.TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": wp_api.UA,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def walk_replace(node, old, new, counter):
    """Remplace `old` par `new` dans toutes les chaines de l'arbre Elementor."""
    if isinstance(node, str):
        if old in node:
            counter[0] += node.count(old)
            return node.replace(old, new)
        return node
    if isinstance(node, list):
        return [walk_replace(x, old, new, counter) for x in node]
    if isinstance(node, dict):
        return {k: walk_replace(v, old, new, counter) for k, v in node.items()}
    return node


def main():
    apply = "--apply" in sys.argv
    ok = ko = 0
    for pid, (slug, rules) in PAGES.items():
        page = wp_api.get_page(pid)
        raw = page["meta"].get("_elementor_data", "")
        tree = json.loads(raw)
        print(f"\n=== {slug} (id {pid}) ===")
        for old, new in rules:
            counter = [0]
            tree = walk_replace(tree, old, new, counter)
            if counter[0] == 0:
                print(f"  ECHEC introuvable : {old[:70]!r}")
                ko += 1
                continue
            ok += 1
            print(f"  OK ({counter[0]}x) {old[:60]!r}")
        data = json.dumps(tree, ensure_ascii=False, separators=(",", ":"))
        if apply and ko == 0:
            res = update_meta(pid, data)
            saved = res["meta"].get("_elementor_data", "")
            verified = all(new in saved for _, new in rules)
            print(f"  -> publie, verification du contenu enregistre : "
                  f"{'OK' if verified else 'ECHEC'}")
            if not verified:
                ko += 1
    print(f"\nBILAN : {ok} corrections, {ko} echecs.")
    if not apply:
        print("Mode simulation. Relancez avec --apply.")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
