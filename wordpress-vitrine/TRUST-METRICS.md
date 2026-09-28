# Indicateurs de preuve sociale (priorité 3)

Équivalent documentaire de la constante `trustMetrics` demandée. Le site étant
géré sous Elementor sans composant dynamique, ces valeurs sont tenues ici et
reportées manuellement dans les pages **une fois vérifiées**.

```js
export const trustMetrics = {
  projectStartYear: null,            // non démontrable à ce jour
  contributingLawyers: null,         // aucun avocat identifié dans l'équipe
  participatingLegalProfessionals: null,
  metricLastUpdatedAt: "2026-07-28",
};
```

## Pourquoi aucun chiffre n'est publié

**Année de naissance du projet — `null`.** Trois dates existent, aucune ne
démontre le démarrage du projet Lumen Juris :

| Date | Ce qu'elle prouve réellement |
|---|---|
| 13/06/2018 | Immatriculation de l'entreprise (SIREN 840406342). Antérieure au projet et sans lien établi avec lui. |
| 27/03/2026 | Premier commit du dépôt applicatif, mais son message est « Initial clean commit » : c'est une réinitialisation de dépôt, pas le début du développement. |
| — | Aucune trace du premier prototype ni du lancement public. |

La page « Qui sommes-nous » raconte donc l'histoire du projet sans avancer
d'année. **Pour publier une date**, indiquez laquelle des quatre natures elle
recouvre (création de l'entreprise, début du projet, premier prototype,
lancement public) et la formulation reprendra exactement cette nature.

**Nombre d'avocats — `null`.** L'équipe présentée compte Geoffrey Pin
(co-fondateur), Laurent Beauté (co-fondateur) et Sonia Oufkir, **juriste
consultante**. Aucun avocat n'est identifié. Les mentions « conçu par des
avocats », « approuvé par des avocats » ou « recommandé par des avocats »
seraient donc inexactes et ne doivent pas être employées.

La formulation de repli prévue est utilisée : *« Développé avec les retours de
professionnels du droit »*, sans chiffre.

## Pour publier un chiffre plus tard

Renseignez d'abord la catégorie exacte, car elles ne se cumulent pas :

- avocats cofondateurs ;
- avocats membres permanents de l'équipe ;
- avocats consultants ;
- avocats testeurs ;
- avocats ayant participé à la conception ;
- cabinets partenaires (accord écrit nécessaire).

Formulations autorisées une fois le chiffre vérifié :

- « Développé avec les retours de X avocats et juristes. »
- « X avocats participent actuellement au programme de test. »
- « L'outil est testé par X professionnels du droit, dont Y avocats. »

## Point connexe : les témoignages de la page d'accueil

Trois témoignages sont affichés (Thomas Dupoint, avocat en droit immobilier ;
Antoine Duplessis, dirigeant d'une société de conseil juridique CSE ;
Christine Levêque, acheteuse). Ils n'ont pas été modifiés : réécrire une
citation attribuée à une personne nommée reviendrait à lui prêter des propos
qu'elle n'a pas tenus.

**Décision requise de l'administrateur** : l'un d'eux affirme « Grâce à
l'outil, tout est conforme et je suis plus serein avec mes clients », ce qui
est exactement le type de promesse absolue que la priorité 2 vise à supprimer.
Deux options, à trancher selon que ces témoignages sont authentiques ou non :

1. **Témoignages authentiques** : conserver les propos tels quels (ce sont ceux
   du client), mais obtenir son accord écrit pour la publication nominative.
2. **Témoignages fictifs ou d'illustration** : les retirer. Publier de faux
   avis nominatifs expose à des sanctions au titre des pratiques commerciales
   trompeuses, et le risque de crédibilité est important auprès d'un public
   d'avocats.
