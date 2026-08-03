"""
Construit l'objet et le corps de chaque message a partir des donnees extraites
du site du cabinet. Aucune information n'est inventee : tout ce qui apparait
dans le message vient de prospects.csv, donc d'une page reellement visitee.
"""

# De la plus distinctive a la plus generique : « droit des contrats » est
# present chez presque tous, il ne personnalise rien. « contrats informatiques »
# identifie au contraire precisement le cabinet.
PRIORITE_SPECIALITES = [
    "contrats informatiques",
    "contentieux contractuel",
    "propriete intellectuelle",
    "droit des societes",
    "droit commercial",
    "droit des affaires",
    "droit des contrats",
]


def specialite_principale(specialites):
    """
    specialites est la colonne 'a ; b ; c' produite par l'extraction.
    On retient la plus proche de notre sujet, pas simplement la premiere.
    """
    trouvees = [s.strip().lower() for s in (specialites or "").split(";") if s.strip()]
    for reference in PRIORITE_SPECIALITES:
        for trouvee in trouvees:
            if reference in trouvee or trouvee in reference:
                return reference
    return trouvees[0] if trouvees else ""


def nettoyer_cabinet(cabinet):
    """
    Le nom vient du titre de la page d'accueil : souvent deja lisible, parfois
    charge de mots-cles. On coupe ce qui suit un separateur.
    """
    nom = (cabinet or "").strip()
    for separateur in (" : ", " | ", " - ", " – "):
        if separateur in nom:
            nom = nom.split(separateur)[0].strip()
    return nom[:60]


import re
from html import escape

CALENDLY = "https://calendly.com/meetingreunion/reunion"
TELEPHONE = "+33 1 76 29 43 30"
ADRESSE = "14 rue Berthelot, 95410 Groslay"
SITE = "www.lumenjuris.com"

# Version texte : les clients qui n'affichent pas le HTML voient les URL en clair.
SIGNATURE_TEXTE = f"""Lumen Juris
{TELEPHONE}
Réserver un créneau : {CALENDLY}
{ADRESSE}
https://{SITE}"""


def corps_html(salutation, accroche, expediteur):
    """
    Version HTML du même message : seule différence, le lien Calendly est
    cliquable. Envoyer les deux versions dans le même message est la pratique
    standard et ne pénalise pas la délivrabilité.
    """
    return f"""<html><body style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#222;line-height:1.5">
<p>{escape(salutation)}</p>
<p>Je suis {escape(expediteur['nom'])}, de Lumen Juris, une plateforme française
d'analyse et d'accompagnement sur les contrats.</p>
<p>{escape(accroche)}</p>
<p>Nous intégrons, dans certaines de nos formules, une consultation avec un
avocat. Pourriez-vous m'indiquer vos tarifs pour&nbsp;:</p>
<ul>
<li>une consultation de 30 minutes</li>
<li>une consultation d'une heure</li>
<li>l'analyse rapide d'un contrat</li>
<li>un tarif partenaire en cas de demandes régulières</li>
</ul>
<p>Nous limitons ce réseau à 10 avocats par domaine du droit. Si cela vous
intéresse, il suffit de répondre à ce message avec vos tarifs.</p>
<p>Bien cordialement,<br>{escape(expediteur['nom'])}</p>
<table cellpadding="0" cellspacing="0" style="border-top:1px solid #ddd;padding-top:10px;margin-top:14px">
<tr>
  <td style="padding-right:16px;border-right:1px solid #ddd;vertical-align:top">
    <strong style="font-size:16px;color:#1a56b0">Lumen Juris</strong>
  </td>
  <td style="padding-left:16px;vertical-align:top;font-size:13px;color:#444">
    {TELEPHONE}<br>
    <a href="{CALENDLY}" style="color:#1a56b0">Réserver un créneau</a><br>
    {ADRESSE}<br>
    <a href="https://{SITE}" style="color:#1a56b0">{SITE}</a>
  </td>
</tr>
</table>
</body></html>"""

SIGNATURE_HTML = f"""<table cellpadding="0" cellspacing="0" style="border-top:1px solid #ddd;padding-top:10px;margin-top:14px">
<tr>
  <td style="padding-right:16px;border-right:1px solid #ddd;vertical-align:top">
    <strong style="font-size:16px;color:#1a56b0">Lumen Juris</strong>
  </td>
  <td style="padding-left:16px;vertical-align:top;font-size:13px;color:#444">
    {TELEPHONE}<br>
    <a href="{CALENDLY}" style="color:#1a56b0">Réserver un créneau</a><br>
    {ADRESSE}<br>
    <a href="https://{SITE}" style="color:#1a56b0">{SITE}</a>
  </td>
</tr>
</table>"""


def html_depuis_texte(texte):
    """
    Met en forme un corps ecrit en texte brut, sans signature.

    Sert aux messages rediges au cas par cas plutot que produits par le
    gabarit : on ne sait pas d'avance combien de paragraphes ils auront. Les
    lignes commencant par « - » deviennent une liste a puces, le reste des
    paragraphes. La signature est ajoutee a la fin, identique pour tous.
    """
    blocs = []
    puces = []

    def vider_puces():
        if puces:
            blocs.append("<ul>" + "".join(f"<li>{escape(p)}</li>" for p in puces) + "</ul>")
            puces.clear()

    for ligne in (texte or "").strip().splitlines():
        nettoyee = ligne.strip()
        if not nettoyee:
            vider_puces()
            continue
        if nettoyee.startswith(("- ", "• ", "* ")):
            puces.append(nettoyee[2:].strip())
        else:
            vider_puces()
            blocs.append(f"<p>{escape(nettoyee)}</p>")
    vider_puces()

    return (
        '<html><body style="font-family:Arial,Helvetica,sans-serif;'
        'font-size:14px;color:#222;line-height:1.5">'
        + "".join(blocs) + SIGNATURE_HTML + "</body></html>"
    )


# Un titre de page comme « Avocat droit des affaires à Lille » n'est pas un nom
# de cabinet : l'employer tel quel donne « la pratique de Avocat droit des
# affaires à Lille », qui ne veut rien dire.
DEBUTS_GENERIQUES = (
    "avocat", "avocats", "cabinet", "maitre", "maître", "me ", "droit",
    "juriste", "consultant", "expert", "votre", "notre", "bienvenue",
)


def est_nom_propre(cabinet):
    nom = (cabinet or "").strip()
    if len(nom) < 3:
        return False
    minuscule = nom.lower()
    if minuscule.startswith(DEBUTS_GENERIQUES):
        return False
    # « X à Lyon », « X en droit des affaires » : formulations descriptives.
    if re.search(r"\b(à|a|en|de la|du|des)\s", minuscule) and len(nom.split()) > 3:
        return False
    return True


def ville_depuis(texte):
    """Recupere la ville quand le titre la mentionne : « ... à Lyon »."""
    match = re.search(r"\bà\s+([A-ZÉÈÀ][\wéèêàâîïôûùç-]{2,20})", texte or "")
    return match.group(1) if match else ""


def construire(destinataire, expediteur):
    """
    Renvoie (objet, corps). Le message reste court : une accroche factuelle,
    la proposition, les quatre tarifs, la sortie.
    """
    cabinet = nettoyer_cabinet(destinataire.get("cabinet"))
    specialite = specialite_principale(destinataire.get("specialite"))
    prenom = (destinataire.get("nom") or "").strip()

    if prenom:
        salutation = f"Bonjour {prenom},"
    elif cabinet:
        salutation = "Bonjour,"
    else:
        salutation = "Bonjour,"

    # Accroche et objet : la spécialité réellement affichée sur le site, et le
    # nom du cabinet. Deux messages ne doivent pas avoir le même objet, sinon
    # quarante envois identiques ressemblent à un publipostage.
    domaine = specialite or "droit des contrats"

    ville = ville_depuis(destinataire.get("cabinet"))

    if est_nom_propre(cabinet):
        accroche = (
            f"Je vous écris parce que la pratique de {cabinet} en {domaine} "
            f"correspond à ce que nos utilisateurs nous demandent le plus souvent."
        )
        objet = f"{cabinet} et Lumen Juris : {domaine}"
    elif ville:
        accroche = (
            f"Je vous écris parce que votre pratique en {domaine} à {ville} "
            f"correspond à ce que nos utilisateurs nous demandent le plus souvent."
        )
        objet = f"{domaine.capitalize()} à {ville} : partenariat Lumen Juris"
    else:
        accroche = (
            f"Je vous écris parce que votre pratique en {domaine} "
            f"correspond à ce que nos utilisateurs nous demandent le plus souvent."
        )
        objet = f"{domaine.capitalize()} : partenariat avec Lumen Juris"

    corps = f"""{salutation}

Je suis {expediteur['nom']}, de Lumen Juris, une plateforme française
d'analyse et d'accompagnement sur les contrats.

{accroche}

Nous intégrons, dans certaines de nos formules, une consultation avec un
avocat. Pourriez-vous m'indiquer vos tarifs pour :

- une consultation de 30 minutes
- une consultation d'une heure
- l'analyse rapide d'un contrat
- un tarif partenaire en cas de demandes régulières

Nous limitons ce réseau à 10 avocats par domaine du droit. Si cela vous
intéresse, il suffit de répondre à ce message avec vos tarifs.

Bien cordialement,

{expediteur['nom']}
{SIGNATURE_TEXTE}"""

    return objet[:120], corps, corps_html(salutation, accroche, expediteur)
