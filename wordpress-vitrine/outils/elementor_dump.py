# -*- coding: utf-8 -*-
"""Liste les textes editables d'une page Elementor, avec l'identifiant du widget.

Usage : python elementor_dump.py <page_id> [motif]
"""
import html as H
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wp_api  # noqa: E402

TEXT_KEYS = ("title", "editor", "text", "heading", "description_text", "title_text",
             "tab_title", "tab_content", "html", "button_text", "sub_title",
             "before_text", "highlighted_text", "after_text", "caption")


def walk(node, rows):
    if isinstance(node, dict):
        kind = node.get("widgetType") or node.get("elType") or ""
        settings = node.get("settings", {})
        if isinstance(settings, dict):
            for key in TEXT_KEYS:
                value = settings.get(key)
                if not isinstance(value, str):
                    continue
                stripped = value.strip()
                if len(stripped) < 3 or stripped.startswith(("<style", ".", "#", "/*", "<script")):
                    continue
                clean = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", value))).strip()
                if clean and not re.match(r"^[.#a-z\[-]+\s*\{", clean):
                    rows.append((node.get("id", ""), kind, key, clean))
        for value in node.values():
            walk(value, rows)
    elif isinstance(node, list):
        for item in node:
            walk(item, rows)


def main():
    page_id = int(sys.argv[1])
    pattern = sys.argv[2] if len(sys.argv) > 2 else None
    data = wp_api.get_page(page_id)["meta"].get("_elementor_data", "[]")
    rows = []
    walk(json.loads(data), rows)
    for wid, kind, key, clean in rows:
        if pattern and not re.search(pattern, clean, re.I):
            continue
        print(f"{wid:<10} {kind:<20} {key:<14} {clean[:160]}")


if __name__ == "__main__":
    main()
