# Données : schéma, validation et anonymisation

> Préparation, conception et programmation : **Dr. Okba Ben Atia**

Ce document décrit le format normalisé des données, les contrôles appliqués lors du chargement
et le dispositif d'anonymisation.

---

## 1. Format normalisé

Toute donnée analysée par le projet — collecte publique, export de plateforme, saisie manuelle —
est ramenée à un format tabulaire unique, en CSV ou en JSON.

```csv
platform,source_id,post_id,interaction_id,source_user,target_user,interaction_type,text,timestamp,parent_id,url
```

Exemple :

```csv
facebook,facebook_001,p001,i001,u001,u002,reply,"Exemple de commentaire",2026-01-01T10:00:00,p001,https://...
```

### 1.1 Colonnes

| Colonne            | Type          | Obligatoire | Description |
|--------------------|---------------|-------------|-------------|
| `platform`         | chaîne        | oui         | Plateforme d'origine : `facebook`, `x`, `instagram`. Normalisée en minuscules. |
| `source_id`        | chaîne        | oui         | Identifiant de la source étudiée, correspondant à `data/sources.json` (ex. `facebook_001`). |
| `post_id`          | chaîne        | oui         | Identifiant de la publication racine à laquelle l'interaction se rattache. Sert de clé de cascade. |
| `interaction_id`   | chaîne        | **oui**     | Identifiant unique de l'interaction. Une ligne sans cette valeur est ignorée. |
| `source_user`      | chaîne        | **oui**     | Auteur de l'interaction (identifiant brut, pseudonymisé par le pipeline). Une ligne sans auteur est ignorée. |
| `target_user`      | chaîne        | non         | Utilisateur visé. Vide pour une publication d'origine. Détermine l'existence d'un lien dans le réseau. |
| `interaction_type` | énumération   | oui         | `post`, `comment`, `reply`, `mention`, `share`, `repost`, `quote`. |
| `text`             | texte libre   | non         | Contenu textuel. Peut être vide (partage sans commentaire). |
| `timestamp`        | date ISO 8601 | non         | Horodatage, par exemple `2026-01-01T10:00:00`. Une valeur illisible est signalée, pas bloquante. |
| `parent_id`        | chaîne        | non         | Identifiant de l'élément parent (`post_id` ou `interaction_id`). Base de la reconstruction des cascades. |
| `url`              | chaîne        | non         | URL publique de la source. |

### 1.2 Types d'interaction

| Type      | Crée un lien réseau | Sens |
|-----------|---------------------|------|
| `post`    | non                 | Publication d'origine. `target_user` et `parent_id` restent vides ; `interaction_id` vaut généralement `post_id`. |
| `comment` | oui                 | Commentaire sous une publication. `parent_id` = `post_id`. |
| `reply`   | oui                 | Réponse à un commentaire ou à une autre réponse. `parent_id` = `interaction_id` du parent. |
| `mention` | oui                 | Mention explicite d'un autre utilisateur. |
| `share`   | oui                 | Partage d'une publication. |
| `repost`  | oui                 | Republication (X). |
| `quote`   | oui                 | Citation avec commentaire (X). |

Les publications ne créent pas de lien mais alimentent le compte de messages de leur auteur et
constituent la racine des cascades de propagation.

### 1.3 Variante JSON

Le même schéma est accepté en JSON, sous forme de liste d'objets ou d'objet contenant une clé
`interactions` :

```json
[
  {
    "platform": "x",
    "source_id": "x_001",
    "post_id": "p002",
    "interaction_id": "i004",
    "source_user": "u004",
    "target_user": "u001",
    "interaction_type": "quote",
    "text": "Texte de la citation",
    "timestamp": "2026-01-02T09:05:00",
    "parent_id": "p002",
    "url": "https://x.com/i/status/2087872720012796385"
  }
]
```

---

## 2. Fichiers de données

| Fichier                          | Rôle |
|----------------------------------|------|
| `data/sources.json`              | Déclaration des sources réelles de l'étude (plateforme, identifiant, URL). |
| `data/import_template.csv`       | Modèle vierge commenté pour l'import manuel. |
| `data/sample_interactions.csv`   | Jeu de démonstration **synthétique**. |
| `data/generer_donnees_demo.py`   | Générateur reproductible du jeu de démonstration (graine fixe). |
| `data/collection_report.json`    | Rapport de la tentative de collecte publique, produit par `analysis/collect.py`. |
| `data/imported/`                 | Répertoire d'import des **données réelles** (CSV ou JSON). Ignoré par Git. |
| `data/private/`                  | Sel et table de correspondance d'anonymisation. **Jamais versionné, jamais publié.** |

### 2.1 Priorité des sources de données

Le pipeline applique une règle simple, sans mélange silencieux :

1. si `data/imported/` contient au moins un fichier `.csv` ou `.json`, **seuls** ces fichiers
   sont analysés et le corpus est déclaré **réel** ;
2. sinon, `data/sample_interactions.csv` est utilisé et le corpus est déclaré **synthétique**.

La nature du corpus est inscrite dans chacun des neuf fichiers JSON produits (bloc
`jeu_de_donnees`) et affichée en permanence dans le tableau de bord. Un corpus synthétique
déclenche l'avertissement :

> Données de démonstration synthétiques — les résultats ne constituent pas des résultats
> empiriques.

---

## 3. Validation

La validation est assurée par `analysis/load_data.py`. Tous les messages d'erreur sont rédigés
en français.

### 3.1 Contrôles bloquants

| Situation                                     | Comportement |
|-----------------------------------------------|--------------|
| Fichier introuvable / aucun jeu de données     | Erreur explicite renvoyant vers `data/import_template.csv` et le générateur de démonstration. |
| Fichier vide                                   | Erreur : « fichier vide (aucune donnée lisible) ». |
| CSV illisible                                  | Erreur : « CSV invalide » avec le détail de l'analyseur. |
| JSON illisible                                 | Erreur : « JSON invalide » avec la position de l'erreur. |
| Colonne obligatoire manquante                  | Erreur listant les colonnes manquantes **et** les colonnes attendues. |
| Aucune interaction exploitable après filtrage  | Erreur explicite. |
| Extension non prise en charge                  | Erreur indiquant les formats acceptés. |

### 3.2 Contrôles non bloquants

Ces situations sont corrigées ou signalées, et remontées dans `overview.json`
(bloc `qualite_donnees`) puis affichées dans le tableau de bord :

| Situation                              | Comportement |
|----------------------------------------|--------------|
| Ligne sans `interaction_id` ou sans `source_user` | Ligne ignorée, comptabilisée dans `lignes_ignorees`. |
| `interaction_id` dupliqué              | Première occurrence conservée, comptabilisée dans `doublons_supprimes`. |
| `timestamp` illisible                  | Horodatage mis à vide, comptabilisé dans `horodatages_invalides`. La ligne reste analysée. |
| Type d'interaction inconnu             | Ligne conservée et marquée `type_reconnu = faux`, type listé dans `types_inconnus`. Aucun lien réseau n'est créé. |
| `text` vide                            | Ligne conservée ; elle est exclue des analyses de contenu (`a_du_texte = faux`). |
| `parent_id` pointant vers une interaction absente | Traité comme une racine de cascade (profondeur 0). |
| Cycle dans les `parent_id`             | Détecté et neutralisé : la profondeur retournée est 0. |

---

## 4. Colonnes ajoutées par le pipeline

Le prétraitement (`analysis/preprocess.py`) enrichit chaque ligne :

| Colonne            | Description |
|--------------------|-------------|
| `raw_text`         | Texte brut, conservé tel quel. |
| `clean_text`       | Texte nettoyé : normalisation Unicode, suppression des URLs et mentions, suppression des diacritiques arabes et du tatweel, harmonisation de l'alef/ya/ta marbuta, réduction des répétitions, passage en minuscules. |
| `hashtags`         | Liste des hashtags relevés (croisillon conservé dans la liste, retiré du texte nettoyé). |
| `mentions`         | Liste des comptes mentionnés. |
| `urls`             | Liste des URLs présentes. |
| `emojis`           | Liste des emojis présents. |
| `langue`           | `fr`, `ar`, `mixte` ou `indetermine`, estimée à partir des systèmes d'écriture. |
| `jetons`           | Jetons complets, mots vides conservés. Utilisés par les classifieurs, qui ont besoin des marques de négation et d'intensité. |
| `jetons_lexicaux`  | Jetons après suppression des mots vides français et arabes. Utilisés pour l'analyse lexicale. |
| `a_du_texte`       | Booléen indiquant si le message comporte un contenu textuel exploitable. |

Les élisions françaises sont découpées (« l'école » → « l » + « école »), afin d'isoler le terme
porteur de sens tout en préservant la négation (« n'est pas »).

Les étapes suivantes ajoutent : `communaute_id`, `communaute`, `sentiment`, `sentiment_score`,
`sentiment_confiance`, `emotion`, `emotion_score`, `emotion_confiance`, `haine_label`,
`haine_confiance`, `haine_signaux`, `auteur_etiquette`.

---

## 5. Anonymisation

Assurée par `analysis/anonymize.py`, avant toute analyse.

### 5.1 Procédure

1. Un **sel** est lu depuis la variable d'environnement `ANONYMIZATION_SALT`. À défaut, il est
   généré une fois et conservé dans `data/private/sel_anonymisation.txt`.
2. Chaque identifiant brut est transformé en pseudonyme technique :
   `usr_` + douze premiers caractères de `HMAC-SHA256(sel, identifiant)`.
3. Les pseudonymes sont triés de façon déterministe et reçoivent une **étiquette d'affichage
   neutre** : « Utilisateur 001 », « Utilisateur 002 »…
4. La table de correspondance est écrite dans `data/private/table_anonymisation.json`,
   répertoire exclu du dépôt.

### 5.2 Garanties

* Aucun identifiant brut, nom, adresse électronique, numéro de téléphone ou donnée personnelle
  n'apparaît dans `public/`.
* Le pseudonyme est stable d'une exécution à l'autre pour un même sel, ce qui permet de comparer
  deux exécutions successives.
* Sans le sel, le pseudonyme n'est pas réversible.
* Les extraits de contenu ne sont publiés dans `public/data/hate_speech.json` **que si le corpus
  analysé est synthétique** : aucun contenu réel d'utilisateur n'est republié.
* Aucun attribut sensible n'est inféré : ni religion, ni origine, ni ethnie, ni orientation
  politique, ni opinion personnelle.

### 5.3 Reproductibilité

Pour obtenir des pseudonymes identiques sur plusieurs machines :

```bash
export ANONYMIZATION_SALT="votre-sel-partage"
python analysis/run_analysis.py
```

Ce sel ne doit jamais être publié : il permettrait de vérifier une correspondance par force
brute sur un ensemble restreint d'identifiants candidats.

---

## 6. Jeu de démonstration

`data/sample_interactions.csv` est **entièrement synthétique** : identifiants, textes et
horodatages sont fabriqués. Il est produit par `data/generer_donnees_demo.py` avec une graine
fixe (`20260119`) et contient 521 interactions, 84 utilisateurs et 14 publications réparties sur
les sept sources déclarées.

Il est construit pour exercer l'ensemble du pipeline : plusieurs groupes latents aux champs
lexicaux distincts, interactions intra et inter-groupes, sentiments variés, exemples de colère,
de soutien, de contenu toxique et de contenu potentiellement haineux, textes en français, en
arabe et mixtes, hashtags, mentions, URLs, emojis, ainsi que des cascades de profondeur
variable.

Les catégories analytiques (sentiment, colère/soutien, toxicité) **ne sont pas écrites dans le
fichier** : elles sont recalculées indépendamment par le pipeline. Le générateur ne fournit donc
aucune vérité terrain, et les résultats obtenus ne mesurent en aucun cas la qualité des
classifieurs.

Régénération :

```bash
python data/generer_donnees_demo.py
```

---

*Préparation, conception et programmation : Dr. Okba Ben Atia*
