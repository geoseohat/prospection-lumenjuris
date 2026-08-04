"""
Genere les recherches Google du jour.

Le fichier recherches.csv d'origine etait fixe : le relancer renvoyait toujours
les memes 40 sites. Ici on combine villes et formulations, et la base retient
les combinaisons deja utilisees pour ne jamais repasser sur les memes.

Le tirage est fait AU HASARD parmi les combinaisons jamais utilisees : deux
jours de suite ne creusent donc jamais le meme sillon, et les professions
comme les villes se melangent au fil des tournees.
"""

import random

VILLES = [
    "Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux", "Lille", "Nantes",
    "Strasbourg", "Montpellier", "Rennes", "Nice", "Grenoble", "Rouen",
    "Dijon", "Angers", "Reims", "Tours", "Clermont-Ferrand", "Le Mans",
    "Amiens", "Metz", "Nancy", "Besancon", "Caen", "Orleans", "Mulhouse",
    "Perpignan", "Limoges", "Brest", "Toulon", "Avignon", "Poitiers",
    "La Rochelle", "Annecy", "Aix-en-Provence", "Versailles", "Nanterre",
    "Boulogne-Billancourt", "Saint-Etienne", "Le Havre", "Nimes", "Pau",
    "Bayonne", "Chambery", "Valence", "Troyes", "Niort", "Lorient",
    "Vannes", "Quimper", "Colmar", "Beauvais", "Evreux", "Chartres",
    "Bourges", "Chalon-sur-Saone", "Macon", "Auxerre", "Albi", "Montauban",
    "Tarbes", "Carcassonne", "Beziers", "Narbonne", "Arles", "Salon-de-Provence",
    "Frejus", "Antibes", "Cannes", "Ajaccio", "Bastia", "Melun", "Meaux",
    "Creteil", "Bobigny", "Evry", "Cergy", "Pontoise", "Saint-Denis",
]

# Chaque entree : (type de cible, formulation de recherche).
# Volontairement large : tous les professionnels du droit susceptibles de
# repondre sur des contrats, pas seulement les avocats.
FORMULATIONS = [
    # --- Avocats, par matiere contractuelle ---
    ("avocat", "avocat droit des contrats"),
    ("avocat", "avocat contentieux contractuel"),
    ("avocat", "avocat rediger contrat commercial"),
    ("avocat", "avocat negociation contractuelle"),
    ("avocat", "avocat rupture contrat"),
    ("avocat", "avocat inexecution contractuelle"),
    ("avocat", "avocat conditions generales de vente"),
    ("avocat", "avocat contrat de prestation de services"),
    ("avocat", "avocat contrat de partenariat commercial"),
    ("avocat", "avocat clause abusive contrat"),
    # --- Avocats, par domaine d'affaires ---
    ("avocat", "avocat droit des affaires"),
    ("avocat", "avocat droit commercial"),
    ("avocat", "avocat droit des societes"),
    ("avocat", "avocat droit de la distribution"),
    ("avocat", "avocat contrat de franchise"),
    ("avocat", "avocat baux commerciaux"),
    ("avocat", "avocat cession de fonds de commerce"),
    ("avocat", "avocat pacte d'associes"),
    ("avocat", "avocat droit de la concurrence"),
    ("avocat", "avocat recouvrement de creances"),
    # --- Avocats, numerique et immateriel ---
    ("avocat", "avocat contrats informatiques"),
    ("avocat", "avocat droit du numerique"),
    ("avocat", "avocat RGPD donnees personnelles"),
    ("avocat", "avocat propriete intellectuelle"),
    ("avocat", "avocat contrat de licence logiciel"),
    ("avocat", "avocat e-commerce"),
    # --- Avocats, secteurs a forte matiere contractuelle ---
    ("avocat", "avocat droit de la construction"),
    ("avocat", "avocat droit immobilier contrats"),
    ("avocat", "avocat contrat de travail employeur"),
    ("avocat", "avocat droit rural contrats"),
    ("avocat", "avocat droit des assurances"),
    ("avocat", "avocat droit bancaire"),
    ("avocat", "avocat droit de la sante contrats"),
    ("avocat", "avocat startup levee de fonds"),
    # --- Cabinets ---
    ("cabinet", "cabinet avocats droit des affaires"),
    ("cabinet", "cabinet avocats droit commercial"),
    ("cabinet", "cabinet avocats droit des contrats"),
    ("cabinet", "cabinet avocats entreprises PME"),
    ("cabinet", "cabinet avocats droit economique"),
    # --- Juristes independants et consultants ---
    ("juriste_independant", "juriste independant droit des contrats"),
    ("juriste_independant", "juriste freelance redaction contrats"),
    ("juriste_independant", "juriste d'entreprise independant"),
    ("juriste_independant", "juriste conseil PME independant"),
    ("professionnel_droit", "consultant juridique contrats entreprises"),
    ("professionnel_droit", "conseil juridique independant entreprises"),
    ("professionnel_droit", "legaltech redaction contrats"),
    ("professionnel_droit", "cabinet conseil en droit des affaires"),
    # --- Autres professions du droit ---
    ("notaire", "notaire droit des affaires"),
    ("notaire", "notaire cession d'entreprise"),
    ("notaire", "notaire baux commerciaux"),
    ("professionnel_droit", "commissaire de justice recouvrement"),
    ("professionnel_droit", "mandataire en droit des societes"),
    ("professionnel_droit", "fiscaliste independant entreprises"),
]


def toutes_les_combinaisons():
    """Ville x formulation, sans ordre particulier : le tirage se fait ailleurs."""
    return [
        (cible, f"{formulation} {ville}")
        for cible, formulation in FORMULATIONS
        for ville in VILLES
    ]


def prochaines_requetes(deja_faites, nombre):
    """
    Tire AU HASARD `nombre` combinaisons jamais utilisees.

    Le hasard remplace l'ancien ordre fixe : chaque tournee pioche des villes
    et des professions differentes, au lieu d'epuiser Paris avant de voir
    la province.
    """
    restantes = [
        (cible, requete)
        for cible, requete in toutes_les_combinaisons()
        if requete not in deja_faites
    ]
    return random.sample(restantes, min(nombre, len(restantes)))


def total_disponible():
    return len(VILLES) * len(FORMULATIONS)
