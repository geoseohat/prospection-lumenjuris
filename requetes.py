"""
Genere les recherches Google du jour.

Le fichier recherches.csv d'origine etait fixe : le relancer renvoyait toujours
les memes 40 sites. Ici on combine villes et specialites, et la base retient
les combinaisons deja utilisees pour ne jamais repasser sur les memes.
"""

VILLES = [
    "Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux", "Lille", "Nantes",
    "Strasbourg", "Montpellier", "Rennes", "Nice", "Grenoble", "Rouen",
    "Dijon", "Angers", "Reims", "Tours", "Clermont-Ferrand", "Le Mans",
    "Amiens", "Metz", "Nancy", "Besancon", "Caen", "Orleans", "Mulhouse",
    "Perpignan", "Limoges", "Brest", "Toulon", "Avignon", "Poitiers",
    "La Rochelle", "Annecy", "Aix-en-Provence", "Versailles", "Nanterre",
]

SPECIALITES = [
    ("avocat", "avocat droit des contrats"),
    ("avocat", "avocat contentieux contractuel"),
    ("avocat", "avocat rediger contrat commercial"),
    ("cabinet", "cabinet avocats droit des affaires"),
    ("cabinet", "cabinet avocats droit commercial"),
    ("avocat", "avocat contrats informatiques"),
    ("avocat", "avocat droit des societes contrats"),
    ("avocat", "avocat negociation contractuelle"),
    ("juriste_independant", "juriste independant droit des contrats"),
    ("professionnel_droit", "consultant juridique contrats entreprises"),
]


def toutes_les_combinaisons():
    """Ville x specialite. L'ordre alterne les villes pour varier les resultats."""
    combos = []
    for specialite_index, (cible, base) in enumerate(SPECIALITES):
        for ville_index, ville in enumerate(VILLES):
            combos.append((cible, f"{base} {ville}", specialite_index, ville_index))
    # trie pour alterner : Paris/contrats, Lyon/contentieux, Marseille/redaction...
    combos.sort(key=lambda c: (c[3] + c[2], c[2]))
    return [(cible, requete) for cible, requete, _, _ in combos]


def prochaines_requetes(deja_faites, nombre):
    """Renvoie les `nombre` premieres combinaisons jamais utilisees."""
    restantes = [
        (cible, requete)
        for cible, requete in toutes_les_combinaisons()
        if requete not in deja_faites
    ]
    return restantes[:nombre]


def total_disponible():
    return len(VILLES) * len(SPECIALITES)
