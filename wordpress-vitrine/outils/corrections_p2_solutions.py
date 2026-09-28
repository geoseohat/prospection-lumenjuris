# -*- coding: utf-8 -*-
"""Priorites 2 et 8 sur les pages « solutions » et « nos engagements »."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import elementor_edit as ee  # noqa: E402

# Bandeau d'hebergement, present a l'identique sur cinq pages.
HEBERGEMENT = ("5767d30", "description_text",
               "Hébergement 100 % français",
               "Hébergement en France : nos serveurs sont situés à Clermont-Ferrand.")

PAGES = {
    2842: [  # Revision contractuelle par IA
        HEBERGEMENT,
        ("2664544", "title",
         "sécurisez vos contrats",
         "Repérez les points de vigilance de vos contrats et préparez vos arbitrages"),
        ("ljprt2", "editor",
         "une première revue fiable et documentée",
         "<p>Contrats fournisseurs, contrats de travail, prestations : les équipes non "
         "juristes obtiennent une première revue documentée, appuyée sur des références "
         "vérifiables, et n’escaladent au juridique que ce qui le mérite.</p>"),
    ],
    2832: [HEBERGEMENT],
    2866: [HEBERGEMENT],
    2852: [HEBERGEMENT],
    2820: [HEBERGEMENT],
    2630: [  # Generateur de contrats
        HEBERGEMENT,
        ("ljprt0", "editor",
         "Générez des trames fiables",
         "<p>Générez des trames de contrat en quelques minutes, appuyées sur les textes "
         "officiels, puis affinez chaque clause. Les références citées vous permettent "
         "de contrôler rapidement ce qui est proposé.</p>"),
        ("ljprt1", "editor",
         "sans expertise juridique",
         "<p>Rédigez vos contrats à partir de zéro : répondez aux questions, complétez "
         "les variables, exportez un document appuyé sur des sources officielles. "
         "Une relecture par un professionnel du droit reste recommandée avant "
         "signature.</p>"),
        ("ljfqt1", "editor",
         "exactement la même valeur juridique",
         "<p>La loi française ne conditionne pas la validité d’un contrat au moyen "
         "utilisé pour le rédiger : ce qui compte est que son contenu respecte le droit "
         "applicable et qu’il soit signé par des parties capables et consentantes. Nos "
         "modèles s’appuient sur la législation en vigueur et citent leurs références, "
         "ce qui facilite la vérification. Pour les situations complexes ou à fort "
         "enjeu, l’outil assiste la rédaction mais ne remplace pas le conseil d’un "
         "professionnel du droit.</p>"),
    ],
}


def main():
    apply = "--apply" in sys.argv
    total_ok = total_ko = 0
    for page_id, edits in PAGES.items():
        print(f"\n=== page {page_id} ===")
        ok, ko = ee.run(page_id, edits, apply=apply, label=str(page_id))
        total_ok += ok
        total_ko += ko
    print(f"\nBILAN solutions : {total_ok} modifications, {total_ko} echecs.")
    sys.exit(1 if total_ko else 0)


if __name__ == "__main__":
    main()
