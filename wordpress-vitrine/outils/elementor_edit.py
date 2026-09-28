# -*- coding: utf-8 -*-
"""Edition ciblee de widgets Elementor par identifiant.

Chaque edition designe (widget_id, cle_de_reglage, ancien_texte_attendu, nouveau).
L'ancien texte sert de garde-fou : si le contenu actuel ne correspond pas, la
modification est refusee. On evite ainsi d'ecraser une version differente de
celle qui a ete auditee.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wp_api  # noqa: E402


def find_widget(node, widget_id):
    if isinstance(node, dict):
        if node.get("id") == widget_id:
            return node
        for value in node.values():
            found = find_widget(value, widget_id)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = find_widget(item, widget_id)
            if found is not None:
                return found
    return None


def apply_edits(tree, edits, label=""):
    """edits : liste de (widget_id, cle, fragment_attendu, nouvelle_valeur)."""
    ok = ko = 0
    for widget_id, key, expected, new_value in edits:
        widget = find_widget(tree, widget_id)
        if widget is None:
            print(f"  ECHEC {label} widget {widget_id} introuvable")
            ko += 1
            continue
        current = widget.get("settings", {}).get(key)
        if not isinstance(current, str):
            print(f"  ECHEC {label} {widget_id}.{key} absent")
            ko += 1
            continue
        if expected and expected not in current:
            plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", current)).strip()
            print(f"  ECHEC {label} {widget_id}.{key} : attendu {expected[:45]!r}, "
                  f"trouve {plain[:70]!r}")
            ko += 1
            continue
        widget["settings"][key] = new_value
        ok += 1
        print(f"  OK    {widget_id}.{key}")
    return ok, ko


def save_page(page_id, tree, post_type="pages"):
    data = json.dumps(tree, ensure_ascii=False, separators=(",", ":"))
    body = json.dumps({"meta": {"_elementor_data": data}}).encode("utf-8")
    req = urllib.request.Request(
        f"{wp_api.SITE}/wp-json/wp/v2/{post_type}/{page_id}",
        data=body,
        headers={"Authorization": f"Basic {wp_api.TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": wp_api.UA},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_tree(page_id, post_type="pages"):
    if post_type == "pages":
        page = wp_api.get_page(page_id)
    else:
        page = json.loads(wp_api.req(
            f"{wp_api.SITE}/wp-json/wp/v2/{post_type}/{page_id}?context=edit"))
    return json.loads(page["meta"]["_elementor_data"])


def run(page_id, edits, apply=False, post_type="pages", label=""):
    tree = load_tree(page_id, post_type)
    ok, ko = apply_edits(tree, edits, label)
    if apply and ko == 0:
        save_page(page_id, tree, post_type)
        saved = json.dumps(load_tree(page_id, post_type), ensure_ascii=False)
        missing = [w for w, k, _, new in edits
                   if json.dumps(new, ensure_ascii=False)[1:-1] not in saved]
        print(f"  -> publie ; widgets non confirmes : {missing or 'aucun'}")
        if missing:
            ko += len(missing)
    return ok, ko
