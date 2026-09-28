# -*- coding: utf-8 -*-
"""Purge le cache Elementor via l'API REST.

Indispensable apres toute modification de `_elementor_data` : Elementor sert
sinon un rendu memorise et les modifications restent invisibles en production,
meme si elles sont bien enregistrees en base.

Usage : python wp_cache.py
"""
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wp_api  # noqa: E402


def purge():
    req = urllib.request.Request(
        f"{wp_api.SITE}/wp-json/elementor/v1/cache",
        headers={"Authorization": f"Basic {wp_api.TOKEN}", "User-Agent": wp_api.UA},
        method="DELETE")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.status


if __name__ == "__main__":
    print(f"Purge du cache Elementor : HTTP {purge()}")
