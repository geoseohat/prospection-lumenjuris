# -*- coding: utf-8 -*-
"""Corrections de la priorite 1 sur les pages Gutenberg de lumenjuris.com.

Chaque correction est un couple (ancien, nouveau) applique sur le contenu brut
de la page. Le script refuse d'appliquer une correction dont l'ancien texte est
absent : cela garantit qu'aucune modification silencieuse n'a lieu.

Usage :
  python corrections_p1.py --dry-run   (affiche les diffs, ne publie rien)
  python corrections_p1.py --apply     (publie via l'API REST)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wp_api  # noqa: E402  (reconfigure deja stdout en UTF-8)

# --------------------------------------------------------------------------
# Mentions legales (id 8)
# --------------------------------------------------------------------------
MENTIONS = [
    # 1.1 Statut juridique : microentreprise, suppression du RCS non applicable
    (
        "<li><strong>Dénomination sociale :</strong> Lumen Juris</li>",
        "<li><strong>Dénomination commerciale :</strong> Lumen Juris</li>",
    ),
    (
        "<li><strong>Statut juridique </strong>: microentreprise</li>",
        "<li><strong>Éditeur :</strong> Geoffrey Pin, entrepreneur individuel</li>\n"
        "<!-- /wp:list-item -->\n\n"
        "<!-- wp:list-item -->\n"
        "<li><strong>Forme juridique :</strong> microentreprise (entreprise individuelle). "
        "En cette qualité, l’éditeur n’est pas doté d’un capital social.</li>",
    ),
    (
        "<li><strong>RCS Pontoise n° [840406342]</strong></li>",
        "<li><strong>Numéro SIREN :</strong> 840406342</li>",
    ),
    (
        "<li><strong>Numéro d’immatriculation au RCS :</strong> 840406342</li>",
        "<li><strong>Numéro SIRET du siège :</strong> 840 406 342 00021</li>",
    ),
    # 1.3 Emails : liens cliquables et correction de rpgd
    (
        "<li><strong>Adresse de courrier électronique :</strong> <a>contact@</a>lumenjuris.com</li>",
        "<li><strong>Adresse de courrier électronique :</strong> "
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a></li>",
    ),
    (
        "Groslay 95410 ou à l'adresse email rgpd@lumenjuris.com.",
        "Groslay 95410, ou à l’adresse "
        "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a>.",
    ),
    # 1.2 Hebergement : distinguer site vitrine et application
    (
        '<h3 class="wp-block-heading">Hébergeur</h3>',
        '<h3 class="wp-block-heading">Hébergement du site vitrine</h3>',
    ),
    (
        "<p>Le site est hébergé par :</p>",
        "<p>Le site internet accessible à l’adresse lumenjuris.com est hébergé par :</p>",
    ),
    (
        "<li><strong>Site internet :</strong> https://www.o2switch.fr/support-hebergeur/</li>\n"
        "<!-- /wp:list-item --></ul>\n<!-- /wp:list -->",
        "<li><strong>Site internet :</strong> "
        "<a href=\"https://www.o2switch.fr/support-hebergeur/\">https://www.o2switch.fr/support-hebergeur/</a></li>\n"
        "<!-- /wp:list-item --></ul>\n<!-- /wp:list -->\n\n"
        "<!-- wp:heading {\"level\":3,\"className\":\"\"} -->\n"
        "<h3 class=\"wp-block-heading\">Hébergement de l’application et des données</h3>\n"
        "<!-- /wp:heading -->\n\n"
        "<!-- wp:paragraph -->\n"
        "<p>L’infrastructure applicative utilisée pour fournir le service Lumen Juris, "
        "ainsi que les sauvegardes associées, est hébergée en France, sur les serveurs "
        "d’o2switch situés à Clermont-Ferrand.</p>\n"
        "<!-- /wp:paragraph -->",
    ),
    # 1.4 Notes internes et placeholders
    (
        '<h2 class="wp-block-heading">Contact – Délégué à la protection des données (si désigné)</h2>',
        '<h2 class="wp-block-heading">Contact</h2>',
    ),
    (
        "<p>Pour toute question, écrivez-nous à contact@lumenjuris.com<br>"
        "Si un <strong>DPO</strong> est désigné : Geoffrey Pin - rpgd@lumenjuris.com</p>",
        "<p>Pour toute question relative au site ou au service : "
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a>.<br>"
        "Pour toute question relative aux données personnelles : "
        "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a>.<br>"
        "Lumen Juris n’a pas désigné de délégué à la protection des données (DPO) à ce jour.</p>",
    ),
    (
        "<p><em>Rappel : toute mise en œuvre de traitements sur un site doit préciser sa "
        "<strong>base légale</strong>, conformément au RGPD.</em></p>\n"
        "<!-- /wp:paragraph -->\n\n"
        "<!-- wp:paragraph -->\n",
        "",
    ),
    # 1.6 Fautes de francais
    (
        "Cet outil est un logiciel de type Saas issu de l'intelligence artificiel et des "
        "bases de données juridiques du gouvernement français.",
        "Cet outil est un logiciel en mode SaaS, qui associe des modèles d’intelligence "
        "artificielle aux bases de données juridiques publiques de l’État français.",
    ),
    (
        "<p>Le site fournit <strong>des informations et des suggestions automatisées</strong> "
        "issues de modèle LLM associés aux bases juridiques "
        "<a href=\"https://www.legifrance.gouv.fr/\">Legifrance</a> du gouvernement français.</p>",
        "<p>Le site fournit <strong>des informations et des suggestions automatisées</strong>, "
        "produites par des modèles de langage et enrichies, lorsque cela est possible, par les "
        "bases juridiques publiques "
        "<a href=\"https://www.legifrance.gouv.fr/\">Légifrance</a>.</p>",
    ),
    (
        "<p>Les modèles LLM associés à l'API fournie par le gouvernement français en open data via "
        "<a href=\"https://piste.gouv.fr/\">l'API  Legifrance</a> fournie par la DILA et accessible "
        "via PISTE (portail d'état). Cette clé permet de proposer des recommandations précises et "
        "adaptées au droit français.",
        "<p>Ces sources sont interrogées via "
        "<a href=\"https://piste.gouv.fr/\">l’API Légifrance</a>, publiée en open data par la DILA "
        "et accessible par le portail d’État PISTE. Elles permettent de proposer des références "
        "rattachées au droit français, que l’utilisateur peut vérifier.",
    ),
    (
        '<h2 class="wp-block-heading">Avertissement important </h2>',
        '<h2 class="wp-block-heading">Avertissement important</h2>',
    ),
]

# --------------------------------------------------------------------------
# CGV (id 20)
# --------------------------------------------------------------------------
CGV = [
    (
        "<li>Statut juridique : microentreprise</li>",
        "<li>Éditeur : Geoffrey Pin, entrepreneur individuel</li>\n"
        "<!-- /wp:list-item -->\n\n"
        "<!-- wp:list-item -->\n"
        "<li>Forme juridique : microentreprise (entreprise individuelle), sans capital social</li>",
    ),
    (
        "<li>RCS Pontoise n° 840 406 342 – SIRET 840 406 342 00021</li>",
        "<li>SIREN 840 406 342 – SIRET du siège 840 406 342 00021 – TVA intracommunautaire FR82840406342</li>",
    ),
    (
        "<li>Directeur de la publication <strong>:</strong> Geoffrey Pin , contact@lumenjuris.com.<br></li>",
        "<li>Directeur de la publication : Geoffrey Pin — "
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a></li>",
    ),
    (
        "<p>Le site est hébergé par :</p>",
        "<p>Le site internet accessible à l’adresse lumenjuris.com est hébergé par :</p>",
    ),
    (
        "<li><strong>Site internet :</strong>&nbsp;https://www.o2switch.fr/support-hebergeur/</li>\n"
        "<!-- /wp:list-item --></ul>\n<!-- /wp:list -->",
        "<li><strong>Site internet :</strong>&nbsp;"
        "<a href=\"https://www.o2switch.fr/support-hebergeur/\">https://www.o2switch.fr/support-hebergeur/</a></li>\n"
        "<!-- /wp:list-item --></ul>\n<!-- /wp:list -->\n\n"
        "<!-- wp:paragraph -->\n"
        "<p>L’infrastructure applicative du service Lumen Juris et les sauvegardes associées "
        "sont hébergées en France, sur les serveurs d’o2switch situés à Clermont-Ferrand.</p>\n"
        "<!-- /wp:paragraph -->",
    ),
    # 1.4 Note interne
    (
        " <em>(Pensez à maintenir la cohérence CGV/Politique de confidentialité et à y "
        "préciser les bases légales et durées de conservation.)</em>",
        "",
    ),
    # 1.3 Emails cliquables + support non verifie
    (
        "s’exercent auprès de rgpd@lumenjuris.com.",
        "s’exercent auprès de "
        "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a>.",
    ),
    (
        "Un <strong>support</strong> est accessible via l'adresse email contact@lumenjuris.com.",
        "Un <strong>support</strong> est accessible à l’adresse "
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a>.",
    ),
    (
        "<li>Contact support : <strong><a>support@lumenjuris.com</a></strong></li>",
        "<li>Contact support : <strong>"
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a></strong></li>",
    ),
    (
        "peut être adressée à <strong><a>rgpd@lumenjuris.com</a></strong>.</li>",
        "peut être adressée à <strong>"
        "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a></strong>.</li>",
    ),
    # 1.6 Phrase bancale
    (
        "assistant d’aide à la <strong>rédaction, l’analyse et la structuration</strong> de "
        "documents juridiques fondé ainsi que toutes fonctionnalités permettant l'aide juridique "
        "et l'assistance dans la gestion des contrats au sein d'une entreprise. Ces fonctionnalités "
        "sont en partie assistée par des modèles d’intelligence artificielle.",
        "outil d’assistance à la <strong>rédaction, à l’analyse et à la structuration</strong> de "
        "documents juridiques, ainsi qu’à la gestion des contrats au sein d’une entreprise. "
        "Certaines de ces fonctionnalités reposent sur des modèles d’intelligence artificielle.",
    ),
]

# --------------------------------------------------------------------------
# CGU (id 2568)
# --------------------------------------------------------------------------
CGU = [
    (
        "<li>microentreprise</li>",
        "<li>Entrepreneur individuel exerçant sous le régime de la microentreprise, "
        "sans capital social</li>",
    ),
    (
        "<li>E-mail : <strong><a>contact@lumenjuris.com</a></strong></li>",
        "<li>E-mail : <strong>"
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a></strong></li>",
    ),
    (
        "<li>E-mail RGPD : <strong><a>rgpd</a></strong>@admin</li>",
        "<li>E-mail RGPD : <strong>"
        "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a></strong></li>",
    ),
    (
        "<li><strong>RCS</strong> : <strong>RCS Pontoise n° [840406342]</strong></li>",
        "<li><strong>Numéro SIREN :</strong> 840406342</li>",
    ),
    (
        "<li><strong>Numéro d’immatriculation au RCS :</strong> 840406342</li>",
        "<li><strong>Numéro SIRET du siège :</strong> 840 406 342 00021</li>",
    ),
    (
        "<p>L’hébergement du site et du Service est assuré par : o2switch infrastructure située "
        "en France, sous réserve d’éventuels services techniques complémentaires utilisés par "
        "Lumen Juris.</p>",
        "<p>Le site vitrine, l’application et les sauvegardes associées sont hébergés en France "
        "par o2switch, Chemin des Pardiaux, 63000 Clermont-Ferrand. Certains services techniques "
        "complémentaires, notamment les fournisseurs de modèles d’intelligence artificielle, "
        "peuvent intervenir dans les conditions décrites par la politique de protection des "
        "données.</p>",
    ),
    (
        "<p><strong><a>contact@lumenjuris.com</a></strong></p>",
        "<p><strong>"
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a></strong></p>",
    ),
    (
        "<p><strong><a>rgpd@lumenjuris.com</a></strong></p>",
        "<p><strong>"
        "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a></strong></p>",
    ),
]

# --------------------------------------------------------------------------
# Politique de confidentialite (id 3)
# --------------------------------------------------------------------------
CONFIDENTIALITE = [
    # 1.1 Suppression de la SAS et du capital social
    (
        "Lumen Juris - SAS au capital de 10 000 € - 14 rue Berthelot, 95410 Groslay, France - "
        "<a>contact@lumenjuris.com</a>.",
        "Lumen Juris — Geoffrey Pin, entrepreneur individuel exerçant sous le régime de la "
        "microentreprise, 14 rue Berthelot, 95410 Groslay, France — "
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a>.",
    ),
    # 1.2 Hebergement reellement verifie
    (
        "<li>Les données du Service (production + sauvegardes) sont <strong>hébergées en France"
        "</strong> chez <strong>Scaleway</strong> (centres de données en région parisienne et en "
        "Île-de-France).</li>",
        "<li>Le site vitrine, l’application et les sauvegardes sont <strong>hébergés en France"
        "</strong> chez <strong>o2switch</strong> (Chemin des Pardiaux, 63000 Clermont-Ferrand).</li>",
    ),
    (
        "<li>Nous n’effectuons <strong>aucun transfert hors UE</strong> pour l’exploitation du "
        "Service, sauf cas ponctuels clairement listés dans la <strong>liste des sous-traitants"
        "</strong> et encadrés par des garanties appropriées le cas échéant.</li>",
        "<li>L’hébergement et le stockage des données sont réalisés en France. Certains "
        "prestataires techniques, notamment les fournisseurs de modèles d’intelligence "
        "artificielle, peuvent traiter des données en dehors de l’Union européenne : ces "
        "traitements sont encadrés par des garanties appropriées, notamment des clauses "
        "contractuelles types. La liste à jour des sous-traitants et de leur localisation est "
        "communiquée sur demande à "
        "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a>.</li>",
    ),
    (
        "<li><strong>Hébergement/Infra</strong> : <strong>Scaleway</strong> (France) , stockage, "
        "sauvegardes, services réseau. </li>",
        "<li><strong>Hébergement et infrastructure</strong> : <strong>o2switch</strong> (France) — "
        "site vitrine, application, stockage, sauvegardes et services réseau.</li>",
    ),
    (
        "<li><strong>Hébergement web</strong> : o2switch (France)</li>",
        "<li><strong>Modèles d’intelligence artificielle</strong> : prestataires spécialisés, "
        "pour la production des suggestions et analyses. La liste nominative et la localisation "
        "des traitements sont communiquées sur demande.</li>",
    ),
    # 1.3 Emails cliquables
    (
        "<li>Pour les données <strong>RT</strong> (compte, facturation, prospection) : "
        "<strong><a>rgpd@lumenjuris.com</a></strong>.</li>",
        "<li>Pour les données <strong>RT</strong> (compte, facturation, prospection) : "
        "<strong><a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a></strong>.</li>",
    ),
    (
        "<li>Pour toute question : <strong><a>rgpd@lumenjuris.com</a></strong>.</li>",
        "<li>Pour toute question : <strong>"
        "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a></strong>.</li>",
    ),
    # 1.6 Espace parasite
    (
        "fondé sur des techniques d’intelligence artificielle .</p>",
        "fondé sur des techniques d’intelligence artificielle.</p>",
    ),
    # Coherence : le DPO n'est pas designe (aligne sur la politique de protection des donnees)
    (
        '<h2 class="wp-block-heading">18) Délégué à la protection des données (DPO)</h2>',
        '<h2 class="wp-block-heading">18) Contact en matière de protection des données</h2>',
    ),
]

# --------------------------------------------------------------------------
# Politique de protection des donnees (id 287)
# --------------------------------------------------------------------------
PROTECTION = [
    (
        "<p>L’infrastructure principale de production et de sauvegarde est hébergée en France "
        "chez Scaleway (région parisienne).</p>",
        "<p>Le site vitrine, l’infrastructure de production et les sauvegardes sont hébergés en "
        "France chez o2switch, Chemin des Pardiaux, 63000 Clermont-Ferrand.</p>",
    ),
    (
        "Le responsable de traitement est Geoffrey Pin, microentrepreneur, dont le siège est "
        "14 rue Berthelot, 95410 Groslay, France, <a>contact@lumenjuris.com</a>.",
        "Le responsable de traitement est Geoffrey Pin, entrepreneur individuel exerçant sous le "
        "régime de la microentreprise sous le nom commercial Lumen Juris, dont le siège est situé "
        "14 rue Berthelot, 95410 Groslay, France — SIREN 840406342 — "
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a>.",
    ),
    (
        "peut être communiquée sur demande à l’adresse : <a>rgpd@lumenjuris.com</a>.",
        "peut être communiquée sur demande à l’adresse "
        "<a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a>.",
    ),
    (
        "Ces droits peuvent être exercés en adressant une demande à : "
        "<strong><a>rgpd@lumenjuris.com</a></strong><br>",
        "Ces droits peuvent être exercés en adressant une demande à "
        "<strong><a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a></strong>.<br>",
    ),
    (
        "via le lien de désinscription ou par courriel adressé à <a>contact@lumenjuris.com</a>.",
        "via le lien de désinscription ou par courriel adressé à "
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a>.",
    ),
    (
        "vous pouvez contacter Lumen Juris à l’adresse suivante : "
        "<strong><a>rgpd@lumenjuris.com</a></strong><br>",
        "vous pouvez contacter Lumen Juris à l’adresse "
        "<strong><a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a></strong>.<br>",
    ),
]

# --------------------------------------------------------------------------
# Politique des cookies (id 281)
# --------------------------------------------------------------------------
COOKIES = [
    (
        "<p>Les informations liées aux traceurs sont traitées sur une infrastructure hébergée en "
        "<strong>France</strong>, auprès de <strong>Scaleway</strong>.</p>",
        "<p>Les informations liées aux traceurs sont traitées sur une infrastructure hébergée en "
        "<strong>France</strong>, auprès d’<strong>o2switch</strong> "
        "(Chemin des Pardiaux, 63000 Clermont-Ferrand).</p>",
    ),
    (
        "<p><strong>Dernière mise à jour : 05/03/202</strong>6</p>",
        "<p><strong>Dernière mise à jour : 05/03/2026</strong></p>",
    ),
    (
        "<p><strong>Geoffrey Pin</strong><br>14 rue Berthelot<br>95410 Groslay – France<br>"
        "<strong><a>contact@lumenjuris.com</a></strong></p>",
        "<p><strong>Geoffrey Pin</strong>, entrepreneur individuel exerçant sous le régime de la "
        "microentreprise sous le nom commercial Lumen Juris<br>14 rue Berthelot<br>"
        "95410 Groslay – France<br><strong>"
        "<a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a></strong></p>",
    ),
    (
        "<p><strong><a>rgpd@lumenjuris.com</a></strong><br>"
        "<strong><a>contact@lumenjuris.com</a></strong></p>",
        "<p><strong><a href=\"mailto:rgpd@lumenjuris.com\">rgpd@lumenjuris.com</a></strong><br>"
        "<strong><a href=\"mailto:contact@lumenjuris.com\">contact@lumenjuris.com</a></strong></p>",
    ),
]

PAGES = {
    8: ("mentions-legales", MENTIONS),
    20: ("conditions-generales-ventes-cgv", CGV),
    2568: ("conditions-generales-dutilisation", CGU),
    3: ("politique-de-confidentialite", CONFIDENTIALITE),
    287: ("politique-de-protection-des-donnees", PROTECTION),
    281: ("politique-des-cookies", COOKIES),
}


def main():
    apply = "--apply" in sys.argv
    out_dir = Path(__file__).parents[1] / "travail" / "corrige"
    out_dir.mkdir(parents=True, exist_ok=True)
    total_ok = total_ko = 0

    for pid, (slug, rules) in PAGES.items():
        page = wp_api.get_page(pid)
        content = page["content"]["raw"]
        print(f"\n=== {slug} (id {pid}) — {len(rules)} corrections ===")
        for old, new in rules:
            n = content.count(old)
            if n == 0:
                print(f"  ECHEC  texte introuvable : {old[:70]!r}")
                total_ko += 1
                continue
            if n > 1:
                print(f"  ATTENTION {n} occurrences : {old[:60]!r}")
            content = content.replace(old, new)
            total_ok += 1
        path = out_dir / f"{slug}--id{pid}.html"
        path.write_text(content, encoding="utf-8")
        print(f"  -> ecrit {path.name}")
        if apply:
            wp_api.update_page(pid, str(path))

    print(f"\nBILAN : {total_ok} corrections appliquees, {total_ko} en echec.")
    if total_ko:
        print("Corrigez les echecs avant de publier.")
        sys.exit(1)
    if not apply:
        print("Mode simulation. Relancez avec --apply pour publier.")


if __name__ == "__main__":
    main()
