# Autoriser l'envoi par l'API Gmail

## Pourquoi

L'environnement d'execution en ligne bloque completement les ports d'envoi de
mail (587 et 465), y compris vers Google. Verifie par trois tests successifs :
connexion refusee en IPv4 comme en IPv6, et services tiers (Brevo, Resend,
Apps Script) refuses par le filtre de sortie.

Seul le trafic web classique passe, et `gmail.googleapis.com` fait partie des
adresses autorisees. L'API Gmail est donc le seul chemin d'envoi disponible en
ligne. Elle marche aussi en local, ce qui permet de tout tester avant de
basculer.

Un mot de passe d'application Gmail ne resout pas le probleme : le blocage se
produit avant toute question de mot de passe.

---

## Etape 1 — Activer l'API Gmail

1. Ouvrir <https://console.cloud.google.com>
2. En haut a gauche, selectionner le projet **plombierqc** (celui qui fait deja
   tourner le Google Sheet).
3. Menu ☰ → **API et services** → **Bibliotheque**
4. Chercher **Gmail API**, l'ouvrir, cliquer **Activer**.

## Etape 2 — Google Auth Platform

Google a refondu cette partie : l'ancien « Ecran de consentement OAuth » est
devenu **Google Auth Platform**, avec les reglages repartis dans le menu de
gauche. Trois rubriques a visiter, dans cet ordre.

### 2a. Branding

Nom de l'application : `Prospection Lumen Juris`.
Adresse e-mail du developpeur : votre adresse Gmail.

Les champs « Page d'accueil », « Regles de confidentialite » et « Conditions
d'utilisation » ne sont necessaires que pour une demande de validation
officielle. Une application utilisee par son seul auteur n'en a pas besoin :
les laisser vides. De meme, l'avertissement « Votre branding doit etre valide »
ne bloque rien ici.

**Domaines autorises** : sans effet pour un client de type « Application de
bureau », qui n'utilise aucun domaine. Ce qui s'y trouve deja peut rester.

Enregistrer, puis passer a la rubrique suivante.

### 2b. Acces aux donnees

C'est ici qu'on declare la permission (l'ancienne etape « champs
d'application »).

1. **Ajouter ou supprimer des champs d'application**
2. Chercher `gmail.send`, cocher `.../auth/gmail.send`
3. **Mettre a jour**, puis **Enregistrer**

C'est la permission la plus etroite qui existe pour Gmail : envoyer, rien
d'autre. Elle ne donne acces ni a la lecture, ni a la suppression de vos
messages.

### 2c. Audience

> ⚠️ **Le point le plus important de toute la procedure.**

1. Type d'utilisateur : **Externe**.
2. Cliquer **PUBLIER L'APPLICATION** (passer de « Test » a « En production »).

Tant que l'application reste en mode Test, Google fait expirer l'autorisation
**au bout de 7 jours** : la routine s'arreterait d'envoyer sans prevenir, un
matin, une semaine apres la mise en service. C'est une panne qu'on met des
jours a comprendre.

Google previendra que l'application n'est pas validee. C'est normal et sans
consequence ici : la validation officielle ne sert que pour une application
distribuee au public. La seule trace visible sera un ecran d'avertissement au
moment d'autoriser, a l'etape 4.

## Etape 3 — Creer l'identifiant

Menu de gauche → **Clients**

1. **Creer un client**
2. Type d'application : **Application de bureau**
3. Nom : `Prospection` → **Creer**
4. **Telecharger le JSON**, le renommer `client_secret.json`, et le deposer
   dans le dossier `bot-mails`.

Ce fichier est exclu du depot : il ne partira jamais sur GitHub.

## Etape 4 — Autoriser chaque adresse

Dans le dossier `bot-mails`, une commande par adresse expeditrice :

```bash
python autoriser-gmail.py geoffrey
```

Le navigateur s'ouvre. Se connecter **avec l'adresse concernee**, cliquer
**Autoriser**. Google affichera « Google n'a pas valide cette application » :
cliquer **Parametres avances** → **Continuer vers Prospection Lumen Juris**.
C'est normal pour une application qui n'est utilisee que par son auteur.

Recommencer pour la deuxieme adresse :

```bash
python autoriser-gmail.py edouard
```

Chaque commande ecrit un fichier `gmail-<cle>.json`, egalement exclu du depot.

## Etape 5 — Verifier

```bash
python envoi_gmail.py --test geoffrey
```

Un message doit arriver dans la boite correspondante. S'il arrive, le chemin
d'envoi utilisable en ligne fonctionne.

---

## Le cas de contact@lumenjuris.com

Son serveur n'est pas chez Google : il reste injoignable depuis le cloud, quel
que soit le chemin.

Il existe une solution de contournement. Si cette adresse est declaree comme
alias d'envoi dans Gmail (**Parametres → Comptes et importation → Envoyer des
e-mails en tant que**), alors l'API Gmail peut envoyer en son nom, et les trois
expediteurs sont conserves.

Sans cet alias : deux expediteurs au lieu de trois, donc 40 emails par jour au
lieu de 60.

---

## Passage en ligne

En ligne il n'y a pas de fichiers, seulement des variables d'environnement.
Le contenu de chaque `gmail-<cle>.json` devient une variable :

| Variable | Contenu |
|---|---|
| `GMAIL_TOKEN_GEOFFREY` | contenu de `gmail-geoffrey.json` |
| `GMAIL_TOKEN_EDOUARD` | contenu de `gmail-edouard.json` |

Le JSON brut ou sa version encodee en base64 sont acceptes, comme pour
`GOOGLE_SERVICE_ACCOUNT_JSON`. La version base64 tient sur une seule ligne et
evite les problemes de guillemets.
