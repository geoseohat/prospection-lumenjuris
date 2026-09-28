# -*- coding: utf-8 -*-
"""Priorite 6 : page « Nos engagements » (2832) transformee en page
« Securite et confidentialite » complete.

Reecrit les sections existantes et ajoute les sections manquantes :
tableau de conservation, mesures d'acces et de securite, liste des
sous-traitants, entrainement de l'IA, contact.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import elementor_edit as ee  # noqa: E402

PAGE = 2832

# --- Styles des tableaux : encapsules pour rester lisibles sur mobile -------
TABLE_CSS = (
    "<style>"
    ".lj-tbl-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:8px 0 4px}"
    ".lj-tbl{width:100%;min-width:620px;border-collapse:collapse;font-size:15px}"
    ".lj-tbl caption{text-align:left;font-weight:600;padding:0 0 10px;font-size:16px}"
    ".lj-tbl th,.lj-tbl td{border:1px solid #E5E7EB;padding:10px 12px;text-align:left;"
    "vertical-align:top;line-height:1.55}"
    ".lj-tbl thead th{background:#F3F6FB;font-weight:600}"
    ".lj-tbl tbody tr:nth-child(even){background:#FAFBFD}"
    "</style>"
)

CONSERVATION = TABLE_CSS + (
    '<div class="lj-tbl-wrap">'
    '<table class="lj-tbl">'
    '<caption>Durées de conservation appliquées</caption>'
    "<thead><tr><th scope=\"col\">Type de donnée</th><th scope=\"col\">Finalité</th>"
    "<th scope=\"col\">Durée active</th><th scope=\"col\">Sauvegardes</th>"
    "<th scope=\"col\">Suppression</th></tr></thead><tbody>"
    "<tr><td>Documents et contenus importés</td><td>Exécution de l’analyse demandée</td>"
    "<td>Jusqu’à suppression par le client ou fin du contrat</td><td>Cycle glissant de 30 jours</td>"
    "<td>Purge dans un délai opérationnel maximal de 30 jours</td></tr>"
    "<tr><td>Compte utilisateur</td><td>Authentification et administration du compte</td>"
    "<td>Durée de la relation contractuelle</td><td>Cycle glissant de 30 jours</td>"
    "<td>Archivage puis suppression à l’issue des obligations légales</td></tr>"
    "<tr><td>Facturation et pièces comptables</td><td>Obligation légale</td>"
    "<td>10 ans</td><td>Incluses dans le cycle de sauvegarde</td>"
    "<td>Suppression au terme du délai légal</td></tr>"
    "<tr><td>Journaux techniques et de sécurité</td><td>Sécurité et détection d’anomalies</td>"
    "<td>90 jours</td><td>Non conservés au-delà</td>"
    "<td>Suppression automatique, sauf incident en cours d’investigation</td></tr>"
    "<tr><td>Préférences de consentement aux cookies</td><td>Preuve du consentement</td>"
    "<td>6 mois</td><td>Sans objet</td><td>Nouvelle demande de préférence à l’expiration</td></tr>"
    "<tr><td>Cookies non essentiels</td><td>Mesure d’audience et confort</td>"
    "<td>13 mois maximum</td><td>Sans objet</td><td>Expiration automatique</td></tr>"
    "</tbody></table></div>"
    "<p>Ces durées correspondent à celles décrites dans notre "
    "<a href=\"https://www.lumenjuris.com/politique-de-protection-des-donnees/\">"
    "politique de protection des données</a>.</p>"
)

SOUS_TRAITANTS = TABLE_CSS + (
    '<div class="lj-tbl-wrap">'
    '<table class="lj-tbl">'
    '<caption>Principaux sous-traitants au 28 juillet 2026</caption>'
    "<thead><tr><th scope=\"col\">Prestataire</th><th scope=\"col\">Service</th>"
    "<th scope=\"col\">Données concernées</th><th scope=\"col\">Localisation</th>"
    "<th scope=\"col\">Garanties</th></tr></thead><tbody>"
    "<tr><td>o2switch</td><td>Hébergement du site, de l’application et des sauvegardes</td>"
    "<td>Ensemble des données du service</td><td>Clermont-Ferrand, France</td>"
    "<td>Traitement sur le territoire national, engagement contractuel de confidentialité</td></tr>"
    "<tr><td>Fournisseur de modèles d’intelligence artificielle</td>"
    "<td>Production des analyses et suggestions</td>"
    "<td>Extraits de documents soumis à l’analyse</td>"
    "<td>Communiquée sur demande ; un traitement hors Union européenne est possible</td>"
    "<td>Clauses contractuelles types et engagement de non-réutilisation à des fins "
    "d’entraînement</td></tr>"
    "<tr><td>Stripe</td><td>Encaissement des abonnements</td>"
    "<td>Données de facturation, moyens de paiement tokenisés</td><td>Union européenne</td>"
    "<td>Prestataire de services de paiement agréé</td></tr>"
    "<tr><td>DocuSign</td><td>Signature électronique avancée</td>"
    "<td>Documents soumis à signature et identité des signataires</td>"
    "<td>Union européenne</td>"
    "<td>Prestataire de services de confiance au sens du règlement eIDAS</td></tr>"
    "</tbody></table></div>"
    "<p>La liste nominative à jour de nos sous-traitants, leur mission et leur "
    "localisation sont communiquées sur demande à "
    "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a>.</p>"
)

DOCUMENTS = (
    "<p>Vos documents sont traités dans un seul but : produire l’analyse ou le document "
    "que vous demandez. Ils ne sont ni revendus, ni transmis à des tiers à des fins "
    "commerciales.</p>"
    "<p><strong>Transmission à un fournisseur d’IA.</strong> Pour produire une analyse, "
    "les extraits de document nécessaires sont transmis à un fournisseur de modèles "
    "d’intelligence artificielle. Les requêtes adressées aux bases juridiques publiques, "
    "elles, sont décorrélées de vos documents : elles portent sur des mots-clés et des "
    "références, non sur votre texte.</p>"
    "<p><strong>Entraînement des modèles.</strong> Les documents importés ne sont pas "
    "utilisés par Lumen Juris pour entraîner ses propres modèles sans consentement "
    "explicite de votre part, et nos fournisseurs sont engagés à ne pas les réutiliser "
    "à cette fin.</p>"
    "<p><strong>Accès humain.</strong> Aucun membre de l’équipe ne consulte vos "
    "documents, sauf dans trois cas : à votre demande expresse dans le cadre d’un "
    "ticket de support, pour un diagnostic technique précis, ou sur réquisition légale. "
    "Cet accès est limité aux personnes habilitées, journalisé et soumis à une "
    "obligation de confidentialité.</p>"
    "<p><strong>Suppression.</strong> Vous pouvez supprimer un document à tout moment "
    "depuis votre espace, ou demander la suppression de l’ensemble de vos contenus à "
    "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a>. La purge intervient "
    "dans un délai opérationnel maximal de 30 jours, sauvegardes comprises.</p>"
)

SECURITE = (
    "<p>Nous ne revendiquons que les mesures effectivement en place. Lumen Juris ne "
    "détient à ce jour aucune certification de type ISO 27001, HDS, SecNumCloud ou "
    "SOC 2, et ne s’en prévaut donc pas.</p>"
    "<ul>"
    "<li><strong>Chiffrement en transit</strong> : l’ensemble des échanges entre votre "
    "navigateur et nos serveurs est protégé par HTTPS/TLS.</li>"
    "<li><strong>Chiffrement au repos</strong> : les volumes de données et les "
    "sauvegardes sont chiffrés.</li>"
    "<li><strong>Contrôle des accès</strong> : principe du moindre privilège, comptes "
    "nominatifs, revues d’accès périodiques.</li>"
    "<li><strong>Journalisation</strong> : les opérations sensibles et les accès aux "
    "contenus sont tracés.</li>"
    "<li><strong>Politique de mots de passe</strong> : exigences de complexité et "
    "possibilité d’activer une authentification à double facteur lorsqu’elle est "
    "proposée.</li>"
    "<li><strong>Sauvegardes</strong> : cycle glissant de 30 jours, chiffrées, avec "
    "plans de continuité et de reprise.</li>"
    "<li><strong>Gestion des incidents</strong> : en cas de violation de données "
    "susceptible d’engendrer un risque, notification à la CNIL sous 72 heures et "
    "information des clients concernés lorsque le risque est élevé, conformément aux "
    "articles 33 et 34 du RGPD.</li>"
    "</ul>"
)

CONTACT = (
    "<p>Nos équipes répondent directement aux questions de sécurité, d’hébergement et "
    "de conformité.</p>"
    "<ul>"
    "<li>Protection des données et exercice de vos droits : "
    "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a></li>"
    "<li>Toute autre question : "
    "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a></li>"
    "</ul>"
    "<p>Pour le détail des traitements, des bases légales et de vos droits, consultez "
    "notre <a href=\"https://www.lumenjuris.com/politique-de-protection-des-donnees/\">"
    "politique de protection des données</a>.</p>"
)

# --- Reecriture des widgets existants --------------------------------------
EDITS = [
    ("2664544", "title",
     "Sécurité des données",
     "Sécurité et confidentialité : hébergement en France, "
     "traitement de vos documents et conformité RGPD"),

    ("4bbb3a5", "description_text",
     "Notre IA est entraînée sur le droit français",
     "Nos analyses s’appuient sur les sources juridiques françaises, "
     "notamment Légifrance."),

    ("8c185d9", "description_text",
     "Aucune donnée client n'est partagée",
     "Vos documents ne sont ni revendus, ni utilisés pour entraîner nos modèles "
     "sans votre accord."),

    ("eng0t", "editor",
     "Lumen Juris traite des documents parmi les plus sensibles",
     "<p>Lumen Juris traite des documents parmi les plus sensibles de votre "
     "organisation : contrats, clauses, données de vos cocontractants. Cette page "
     "décrit, sans effet d’annonce, où sont hébergées vos données, ce que nous en "
     "faisons, combien de temps nous les conservons, et à qui nous les confions.</p>"),

    ("eng1h", "title", "hébergement souverain",
     "Où sont hébergées vos données"),

    ("eng1t", "editor",
     "votre patrimoine contractuel n’est pas dispersé",
     "<p>Le site vitrine, l’application, les documents que vous importez et les "
     "sauvegardes associées sont hébergés en France, chez o2switch, dont les "
     "serveurs sont situés à Clermont-Ferrand (Chemin des Pardiaux, 63000).</p>"
     "<p>Ces données sont donc traitées sur le territoire national : votre patrimoine "
     "contractuel n’est pas dispersé entre des juridictions dont les régimes de "
     "protection diffèrent. Seule exception, décrite plus bas : les extraits soumis à "
     "l’analyse par un modèle d’intelligence artificielle.</p>"),

    ("eng2h", "title", "Confidentialité et sécurité de vos documents",
     "Ce que nous faisons de vos documents"),

    ("eng2t", "editor", "reste votre contrat", DOCUMENTS),

    ("eng3h", "title", "Une IA nourrie par les sources publiques",
     "Les sources juridiques que nous interrogeons"),

    ("eng4h", "title", "Notre conformité RGPD",
     "Accès, sécurité et conformité RGPD"),

    ("eng4t", "editor", "case à cocher", SECURITE),

    ("ljctah", "title", "Une question sur la sécurité",
     "Une question sur la sécurité de vos données ?"),

    ("ljctat", "editor", "sans jargon commercial", CONTACT),
]

# La liste a puces revendiquait un « referent protection des donnees »
# designe, ce qui contredisait la politique de protection des donnees
# (« Lumen Juris n'a pas designe de DPO a ce jour »).
ICON_LIST = [
    {"_id": "e40",
     "text": "<strong>Point de contact dédié</strong> : "
             "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a>. "
             "Lumen Juris n’a pas désigné de délégué à la protection des données "
             "au sens de l’article 37 du RGPD.",
     "selected_icon": {"value": "fas fa-check-circle", "library": "fa-solid"}},
    {"_id": "e41",
     "text": "<strong>Registre des traitements</strong> tenu et mis à jour.",
     "selected_icon": {"value": "fas fa-check-circle", "library": "fa-solid"}},
    {"_id": "e42",
     "text": "<strong>Droits des personnes</strong> : procédure d’exercice des droits "
             "d’accès, de rectification, d’effacement, de limitation, d’opposition et "
             "de portabilité, avec réponse sous un mois.",
     "selected_icon": {"value": "fas fa-check-circle", "library": "fa-solid"}},
    {"_id": "e43",
     "text": "<strong>Sous-traitants sélectionnés</strong> sur leurs garanties de "
             "sécurité et de conformité, et encadrés contractuellement.",
     "selected_icon": {"value": "fas fa-check-circle", "library": "fa-solid"}},
]


def build_section(section_id, title, html):
    """Cree une section pleine largeur : un titre et un bloc de texte."""
    return {
        "id": section_id,
        "elType": "container",
        "settings": {
            "flex_direction": "column",
            "content_width": "boxed",
            "flex_gap": {"unit": "px", "size": 18, "column": "18", "row": "18"},
            "padding": {"unit": "px", "top": "0", "right": "20", "bottom": "70",
                        "left": "20", "isLinked": False},
        },
        "elements": [
            {"id": section_id + "h", "elType": "widget", "widgetType": "heading",
             "settings": {"title": title, "header_size": "h2"}, "elements": []},
            {"id": section_id + "t", "elType": "widget", "widgetType": "text-editor",
             "settings": {"editor": html}, "elements": []},
        ],
    }


NEW_SECTIONS = [
    ("engcons", "Combien de temps nous conservons vos données", CONSERVATION),
    ("engsstr", "Nos sous-traitants", SOUS_TRAITANTS),
]


def main():
    apply = "--apply" in sys.argv
    tree = ee.load_tree(PAGE)
    ok, ko = ee.apply_edits(tree, EDITS, "engagements")

    # Liste a puces RGPD
    widget = ee.find_widget(tree, "eng4l")
    if widget is None:
        print("  ECHEC eng4l introuvable")
        ko += 1
    else:
        widget["settings"]["icon_list"] = copy.deepcopy(ICON_LIST)
        ok += 1
        print("  OK    eng4l.icon_list")

    # Insertion des nouvelles sections juste avant l'appel a l'action final
    ids = [c.get("id") for c in tree]
    if "ljcta9" not in ids:
        print("  ECHEC conteneur d'appel a l'action introuvable")
        ko += 1
    else:
        position = ids.index("ljcta9")
        existing = set(ids)
        for offset, (sid, title, html) in enumerate(NEW_SECTIONS):
            if sid in existing:
                print(f"  INFO  section {sid} deja presente, remplacee")
                tree[ids.index(sid)] = build_section(sid, title, html)
            else:
                tree.insert(position + offset, build_section(sid, title, html))
                ok += 1
                print(f"  OK    section {sid} ajoutee")

    if apply and ko == 0:
        ee.save_page(PAGE, tree)
        saved = json.dumps(ee.load_tree(PAGE), ensure_ascii=False)
        checks = {
            "tableau de conservation": "Durées de conservation appliquées",
            "tableau sous-traitants": "Principaux sous-traitants",
            "absence de DPO": "n’a pas désigné de délégué",
            "hebergeur nomme": "o2switch",
        }
        for label, needle in checks.items():
            state = "OK" if json.dumps(needle, ensure_ascii=False)[1:-1] in saved else "ABSENT"
            print(f"  verification {label} : {state}")
            if state == "ABSENT":
                ko += 1

    print(f"\nBILAN nos-engagements : {ok} modifications, {ko} echecs.")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
