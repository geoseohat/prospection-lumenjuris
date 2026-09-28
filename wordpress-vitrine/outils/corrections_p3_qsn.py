# -*- coding: utf-8 -*-
"""Priorite 3 : preuve sociale mesuree sur « Qui sommes-nous » (page 607).

Aucun chiffre n'est publie : ni l'annee de naissance du projet, ni un nombre
d'avocats, ne sont aujourd'hui demontrables. Voir wordpress-vitrine/TRUST-METRICS.md.
Le script nettoie aussi des residus de blocs Gutenberg visibles dans le texte.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import elementor_edit as ee  # noqa: E402

HISTOIRE = (
    "<p>L’idée de Lumen Juris est née d’un constat : dans les cabinets comme dans les "
    "services juridiques, on manque de temps. Les contrats s’enchaînent, la conformité "
    "demande des vérifications minutieuses, et la recherche juridique passe souvent "
    "après l’urgence du quotidien.</p>"
    "<p>Sonia, juriste de métier, s’est demandé : « et si on s’aidait de l’IA pour "
    "gagner du temps au quotidien, sans altérer la qualité ? ». Geoffrey, Laurent et "
    "Sonia ont assemblé un premier test : un outil qui aide à relire, structurer et "
    "pointer les zones à vérifier.</p>"
    "<p>Geoffrey et Laurent ont poussé le prototype côté code, et Geoffrey a mis en "
    "forme une première version utilisable. Puis nous l’avons fait essayer à plusieurs "
    "juristes, ce qui a confirmé que l’outil était utile et pertinent pour les "
    "professionnels du droit.</p>"
    "<p>Ce qui a fait la différence, c’est l’ouverture des données juridiques "
    "françaises par Légifrance : pouvoir interroger les textes officiels et s’en servir "
    "pour guider une relecture plus rapide, en rattachant chaque suggestion à une "
    "référence vérifiable.</p>"
    "<p>Pas pour remplacer le raisonnement d’un juriste, mais pour lui faire gagner du "
    "temps sur la rédaction, la révision et les vérifications de conformité.</p>"
    "<p>Aujourd’hui, Lumen Juris, c’est une petite équipe qui aime les choses bien "
    "faites : un outil d’assistance qui alerte, compare, met en contexte et rappelle "
    "les points à vérifier. Ni promesses miracles, ni jargon : un compagnon de travail "
    "qui vous rend du temps et de la clarté, pour que l’essentiel, votre jugement, "
    "reste au centre.</p>"
    "<p><strong>Le projet est développé avec les retours de professionnels du droit</strong>, "
    "qui testent l’outil sur leurs propres dossiers et orientent ses évolutions.</p>"
)

EDITS = [
    ("af0bd21", "editor", "data-start", HISTOIRE),
    ("qsnt3", "editor",
     "Une juriste de métier et deux profils tech",
     "<p>Une juriste de métier et deux profils techniques, complémentaires depuis le "
     "premier prototype, épaulés par les retours de professionnels du droit qui "
     "utilisent l’outil.</p>"),
    ("qsnt2", "editor",
     "Une IA appuyée sur les sources officielles françaises",
     "<p>Une IA appuyée sur les sources juridiques officielles françaises, pensée pour "
     "assister le professionnel du droit et non pour le remplacer. Chaque suggestion "
     "reste soumise à son contrôle.</p>"),
]


def main():
    apply = "--apply" in sys.argv
    ok, ko = ee.run(607, EDITS, apply=apply, label="qui-sommes-nous")
    print(f"\nBILAN qui-sommes-nous : {ok} modifications, {ko} echecs.")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
