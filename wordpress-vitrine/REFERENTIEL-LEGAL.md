# Référentiel légal Lumen Juris — source unique de vérité

Ce document est la **source unique** des informations légales et institutionnelles
publiées sur www.lumenjuris.com. Toute page légale doit reprendre exactement ces
valeurs. Document interne : il n'est pas publié sur le site.

Dernière mise à jour : 28/07/2026.

## Identité de l'éditeur

| Champ | Valeur retenue | Vérification |
|---|---|---|
| Nom commercial | Lumen Juris | — |
| Forme juridique | Microentreprise (entreprise individuelle) | Nature juridique 1000 = personne physique, API Recherche d'entreprises (gouv.fr) |
| Entrepreneur / éditeur | Geoffrey Pin | Déclaré sur CGU et politique de protection des données |
| Capital social | **Sans objet** — une entreprise individuelle n'a pas de capital social | Conséquence de la forme juridique |
| SIREN | 840406342 | API Recherche d'entreprises, entreprise active |
| SIRET (siège) | 84040634200021 | idem |
| TVA intracommunautaire | FR82840406342 | Cohérent avec le SIREN (clé 82) |
| Code APE / NAF | 73.11Z | API Recherche d'entreprises |
| Date de création | 13/06/2018 | API Recherche d'entreprises |
| Siège | 14 rue Berthelot, 95410 Groslay, France | Constant sur toutes les pages |
| Directeur de publication | Geoffrey Pin | Constant |
| Téléphone | +33 1 76 29 43 30 | Affiché dans le pied de page |
| RCS | **Ne pas mentionner** | Une microentreprise d'activité libérale (73.11Z) n'est pas immatriculée au RCS. Les pages annonçaient « RCS Pontoise » : mention supprimée au profit du SIREN / SIRET, seuls numéros vérifiés. |

## Adresses de contact

| Usage | Adresse | Statut |
|---|---|---|
| Général | contact@lumenjuris.com | Publiée |
| Données personnelles / RGPD | rgpd@lumenjuris.com | Publiée |
| Support | support@lumenjuris.com | **À VÉRIFIER par l'administrateur** : la boîte existe-t-elle réellement ? En attendant, les CGV renvoient le support vers contact@lumenjuris.com. |

Adresses fautives supprimées : `rpgd@lumenjuris.com` (mentions légales), `rgpd@admin` (CGU).

## Hébergement

| Périmètre | Hébergeur retenu | Vérification |
|---|---|---|
| Site vitrine lumenjuris.com | o2switch — Chemin des Pardiaux, 63000 Clermont-Ferrand, France | DNS : 109.234.161.12, RDAP RIPE → O2SWITCH |
| Application et API | o2switch (mêmes serveurs) | `lumenjurisbackendnodejs.lumenjuris.com` et `backend.python.lumenjuris.com` résolvent vers la même IP o2switch |
| Scaleway | **Non retenu** | Aucune trace de Scaleway dans le code applicatif ni dans le DNS. Les mentions « infrastructure hébergée chez Scaleway » présentes dans la politique de confidentialité, la politique de protection des données et la politique des cookies n'étaient pas vérifiables : elles ont été remplacées par o2switch. |

**Si l'infrastructure migre effectivement vers Scaleway**, mettre à jour ce
document puis les trois politiques, et non l'inverse.

## Points à faire confirmer par l'administrateur

Ces éléments n'ont pas pu être vérifiés techniquement et ne doivent pas être
affirmés sur le site tant qu'ils ne le sont pas :

1. **Fournisseur d'IA.** Le code utilise `OPENAI_API_KEY` et des modèles
   `gpt-4o-mini` (voir `back/.env.example`, `proxy/src/utils/openaiClient.ts`).
   OpenAI est un prestataire dont les traitements peuvent avoir lieu hors UE.
   La politique de confidentialité affirmait « aucun transfert hors UE » : cette
   affirmation a été assouplie. Il faut : (a) confirmer le ou les fournisseurs
   d'IA réellement utilisés en production, (b) vérifier la zone de traitement
   contractuelle, (c) les inscrire dans la liste des sous-traitants.
2. **Chiffrement au repos.** Affirmé dans plusieurs politiques ; à confirmer
   auprès de l'hébergeur avant de le maintenir tel quel.
3. **Boîte support@lumenjuris.com** (voir plus haut).
4. **Date de naissance du projet Lumen Juris** (priorité 3) : l'entreprise a été
   créée le 13/06/2018, ce qui ne correspond pas nécessairement au démarrage du
   projet Lumen Juris. À préciser avant toute publication.
5. **Nombre d'avocats contributeurs** (priorité 3). L'équipe affichée compte une
   juriste consultante (Sonia Oufkir) et deux profils tech ; aucun avocat n'est
   identifié. Ne pas écrire « conçu par des avocats ».
