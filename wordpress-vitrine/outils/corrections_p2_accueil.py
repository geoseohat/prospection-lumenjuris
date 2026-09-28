# -*- coding: utf-8 -*-
"""Priorites 2 et 8 : promesses mesurees et positionnement, page d'accueil (103)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import elementor_edit as ee  # noqa: E402

EDITS = [
    # --- P2.1 : promesses absolues -----------------------------------------
    ("1a26ae7", "title",
     "sécurisez vos contrats",
     "Gagnez du temps sur vos contrats et repérez les points de vigilance"),

    ("9ad9a33", "title",
     "IA + Légifrance = conforme",
     "Références issues notamment de Légifrance"),

    ("4209ae08", "title",
     "100 % français",
     "Un outil français, appuyé sur les sources juridiques officielles"),

    ("2b5bfbcc", "title",
     "5 heures gagnées",
     "Première lecture accélérée"),

    ("2991c659", "editor",
     "alternatives conformes",
     "<p>Téléversez votre contrat au format PDF ou Word. L’outil analyse les clauses, "
     "signale les points de vigilance, propose des reformulations à vérifier et répond "
     "à vos questions dans un espace de discussion dédié.</p>"
     "<p>Les analyses sont enrichies, lorsque des références sont disponibles, par les "
     "sources juridiques officielles françaises, notamment Légifrance.</p>"),

    # --- P2.1 : explication de la fiabilite --------------------------------
    ("7633397", "title",
     "vraiment fiable",
     "Quelle confiance accorder aux résultats ?"),

    ("2c9c2a7", "editor",
     "la plus fiable et pertinente juridiquement",
     "<p>Lumen Juris associe l’intelligence artificielle à des sources juridiques "
     "françaises, notamment Légifrance. Lorsque des références sont disponibles, elles "
     "sont présentées afin de permettre à l’utilisateur de vérifier les suggestions.</p>"
     "<p>Concrètement, l’outil interroge Légifrance via son API, récupère les textes "
     "pertinents, puis s’appuie sur ces références pour produire ses analyses. Chaque "
     "alerte est accompagnée de la référence correspondante et d’un surlignage dans "
     "le document.</p>"
     "<p>Comme tout outil fondé sur l’intelligence artificielle, Lumen Juris peut "
     "produire des erreurs ou des approximations : chaque résultat doit être contrôlé "
     "par un professionnel compétent.</p>"),

    # --- P2.1 : signaler, ne pas garantir la detection ---------------------
    ("e8eaeb8", "title",
     "détecte-t-il les clauses interdites",
     "L’outil signale-t-il les clauses potentiellement illicites ou abusives ?"),

    ("acf3f87", "editor",
     "affaiblissent vos intérêts",
     "<p>Il signale les clauses qui paraissent illicites ou abusives au regard des "
     "textes identifiés, et indique la référence sur laquelle repose ce signalement.</p>"
     "<p>Il attire également l’attention sur les clauses qui vous semblent "
     "défavorables, et propose des pistes de reformulation appuyées sur le droit "
     "français. Aucun outil ne peut garantir une détection exhaustive : ces "
     "signalements constituent une aide à la relecture, que le professionnel valide.</p>"),

    # --- P2 : chiffres invérifiables ---------------------------------------
    ("c7bbfad", "editor",
     "nos équipes ont constaté entre 30 et 60",
     "<p>Le gain dépend de la taille et de la qualité des documents, ainsi que de la "
     "maturité de votre processus de relecture.</p>"
     "<p>L’outil prend en charge la première passe : repérage des clauses sensibles, "
     "points de vigilance et synthèse. Le professionnel confirme, ajuste et se "
     "concentre sur l’analyse plutôt que sur la lecture exhaustive.</p>"),

    # --- P1.4 residuelle : contenu genere non nettoye (attributs data-start) -
    ("4751d11", "editor",
     "data-start",
     "<p>Le traitement des documents poursuit une finalité déterminée : l’analyse "
     "juridique demandée par l’utilisateur. Les données sont hébergées en France, les "
     "accès sont restreints et journalisés, et les durées de conservation sont "
     "précisées dans notre politique de protection des données.</p>"
     "<p>Les documents importés ne sont pas utilisés par Lumen Juris pour entraîner "
     "ses propres modèles sans consentement explicite.</p>"),

    ("c5464db", "editor",
     "data-start",
     "<p>L’outil ne se contente pas d’une réponse générique : il interroge les sources "
     "juridiques françaises, notamment Légifrance, et rattache ses analyses aux textes "
     "identifiés. Vous savez ainsi sur quoi repose chaque suggestion, et vous pouvez "
     "la vérifier.</p>"),

    ("149bff95", "editor",
     "data-start",
     "<ul>"
     "<li>Points de vigilance identifiés : responsabilité, résiliation, pénalités, "
     "protection des données…</li>"
     "<li>Relecture plus rapide : suggestions de reformulation et modèles internes "
     "pour standardiser vos contrats.</li>"
     "<li>Comparaison facilitée : mise en regard de vos standards internes et des "
     "pratiques du marché.</li>"
     "<li>Moins d’allers-retours : un espace de discussion pour clarifier une clause "
     "sans quitter le document.</li>"
     "</ul>"),

    ("79ba844", "editor",
     "Révisez votre contrat automatiquement",
     "<ol>"
     "<li>Déposez votre document au format PDF ou Word.</li>"
     "<li>Précisez l’analyse que vous souhaitez obtenir.</li>"
     "<li>Parcourez les points de vigilance : surlignages, suggestions de "
     "reformulation et clauses manquantes.</li>"
     "<li>Interrogez l’espace de discussion sur les clauses signalées.</li>"
     "<li>Exportez une synthèse des principaux points à vérifier.</li>"
     "<li>Appuyez-vous sur nos modèles de clauses.</li>"
     "</ol>"),
]


def main():
    apply = "--apply" in sys.argv
    ok, ko = ee.run(103, EDITS, apply=apply, label="accueil")
    print(f"\nBILAN accueil : {ok} modifications, {ko} echecs.")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
