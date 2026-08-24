# Étude de la polarisation et de la propagation du discours de haine sur les réseaux sociaux

**Analyse de réseaux, détection de communautés et analyse automatique du contenu**

> **Préparation, conception et programmation : Dr. Okba Ben Atia**

MVP académique léger, reproductible et déployable, permettant d'étudier la polarisation,
les communautés et la propagation du discours de haine autour de sujets sensibles
(arabisation, religion, immigration, identité et questions sociales et politiques connexes).

L'ensemble des calculs est réalisé **hors ligne en Python**. Le tableau de bord Next.js ne fait
que restituer des résultats déjà produits : il ne nécessite aucun serveur Python permanent,
aucune base de données et aucun modèle d'apprentissage automatique côté navigateur.

---

## Architecture

```
URLs / CSV / JSON
        ↓
Pipeline Python hors ligne   (analysis/)
        ↓
Résultats JSON               (public/data/*.json)
        ↓
Tableau de bord Next.js      (src/)
        ↓
Vercel
```

Aucune base de données, aucun backend permanent, aucune infrastructure complexe.

---

## Démarrage rapide

### 1. Pipeline d'analyse

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optionnel : tentative de collecte publique des sources (métadonnées uniquement)
python analysis/collect.py

# Analyse complète et génération des JSON
python analysis/run_analysis.py
```

Le pipeline utilise **les données réelles** présentes dans `data/imported/` si elles existent.
En leur absence, il retombe sur le jeu de démonstration synthétique
`data/sample_interactions.csv`. Les deux ne sont **jamais mélangés silencieusement** : la nature
du corpus est affichée en permanence dans le tableau de bord.

### 2. Tableau de bord

```bash
npm install
npm run dev     # développement — http://localhost:3000
npm run build   # production
npm run lint
```

### 3. Tests

```bash
pytest
```

---

## Sources de l'étude

Les sept publications constituant les cas d'étude initiaux sont déclarées dans
`data/sources.json` :

| Plateforme | Identifiant     | URL |
|------------|-----------------|-----|
| Facebook   | `facebook_001`  | https://www.facebook.com/share/v/18hGjKiFVK/ |
| Facebook   | `facebook_002`  | https://www.facebook.com/share/p/1HYJ6PKM2Q/ |
| Facebook   | `facebook_003`  | https://www.facebook.com/share/v/1GCZzavgcV/ |
| Facebook   | `facebook_004`  | https://www.facebook.com/share/p/1F5HSSqfkM/ |
| Facebook   | `facebook_005`  | https://www.facebook.com/share/p/18GdU39RoV/ |
| X          | `x_001`         | https://x.com/i/status/2087872720012796385 |
| Instagram  | `instagram_001` | https://www.instagram.com/reel/DbtVlHYABVK/ |

Le statut de collecte réel de chaque source est documenté dans
[`docs/COLLECTE_DES_DONNEES.md`](docs/COLLECTE_DES_DONNEES.md) et affiché sur la page
« Sources étudiées ». **Aucune source n'est présentée comme analysée tant que ses données
n'ont pas été réellement récupérées ou importées.**

> **État de la collecte au 24 août 2026.** Les 14 voies d'accès évaluées (7 pages publiques et
> 7 points d'accès oEmbed officiels) ont **toutes** été refusées par le `robots.txt` des
> plateformes. **0 interaction récupérée automatiquement ; les 7 sources nécessitent un import
> manuel.** Les résultats actuellement publiés proviennent donc d'un **jeu de démonstration
> synthétique**, explicitement signalé sur chaque page du tableau de bord.

---

## Format normalisé des données

```csv
platform,source_id,post_id,interaction_id,source_user,target_user,interaction_type,text,timestamp,parent_id,url
```

Types d'interaction acceptés : `post`, `comment`, `reply`, `mention`, `share`, `repost`, `quote`.

Le pipeline analyse exactement les mêmes données, qu'elles proviennent d'une collecte publique,
d'un export de plateforme, d'un CSV manuel ou d'un JSON. Modèle d'import fourni :
[`data/import_template.csv`](data/import_template.csv). Schéma détaillé :
[`docs/DONNEES.md`](docs/DONNEES.md).

### Import manuel

1. Préparer un fichier CSV ou JSON au format normalisé.
2. Le déposer dans `data/imported/`.
3. Relancer `python analysis/run_analysis.py`.

Dès qu'un fichier est présent dans `data/imported/`, le jeu de démonstration est ignoré et le
tableau de bord bascule en mode « données réelles ».

---

## Ce que produit le pipeline

| Fichier                       | Contenu |
|-------------------------------|---------|
| `public/data/overview.json`   | Indicateurs clés, répartitions, évolution temporelle, qualité des données |
| `public/data/sources.json`    | Statut de collecte réel de chaque source |
| `public/data/network.json`    | Nœuds, liens, métriques structurelles, centralités |
| `public/data/communities.json`| Communautés, modularité, polarisation, matrice d'interactions |
| `public/data/content.json`    | Profils lexicaux par communauté × plateforme |
| `public/data/sentiment.json`  | Sentiment positif / neutre / négatif |
| `public/data/emotions.json`   | Colère / soutien / autre |
| `public/data/hate_speech.json`| Non haineux / toxique / potentiellement haineux |
| `public/data/propagation.json`| Cascades, profondeur, durée, communautés traversées |

Le tableau de bord consomme **uniquement** ces fichiers. Aucune statistique scientifique n'est
écrite en dur dans le code React.

---

## Pages du tableau de bord

Vue d'ensemble · Sources étudiées · Réseau · Communautés · Analyse du contenu ·
Sentiments et émotions · Discours haineux · Propagation · Méthodologie.

Interface entièrement en français, responsive, avec mode clair et mode sombre.

---

## Précautions scientifiques

Le projet maintient rigoureusement la distinction entre des dimensions souvent confondues :

> polarisation ≠ sentiment négatif ≠ colère ≠ toxicité ≠ discours haineux

* Les communautés ne reçoivent que des noms neutres (« Communauté 1 », « Communauté 2 »…).
  **Aucune étiquette idéologique n'est générée automatiquement.**
* On ne parle jamais d'« utilisateur haineux », mais de « contenu classifié comme
  potentiellement haineux ».
* Les classifications de sentiment, de colère/soutien et de toxicité sont **heuristiques et
  indicatives**. Aucune évaluation sur corpus annoté n'a été conduite : **aucune performance
  (précision, rappel, F1) n'est annoncée**.
* Les seuils d'interprétation de la polarisation sont **conventionnels et indicatifs**.
* Aucun attribut sensible n'est inféré : ni religion, ni origine, ni ethnie, ni orientation
  politique, ni opinion personnelle.

---

## Anonymisation

Tous les identifiants d'utilisateurs sont pseudonymisés (HMAC-SHA256 salé) avant toute analyse,
puis remplacés à l'affichage par des étiquettes neutres (« Utilisateur 001 »…). La table de
correspondance reste locale (`data/private/`, exclue du dépôt) et n'est **jamais** publiée dans
`public/`.

---

## Éthique de la collecte

La tentative de collecte publique (`analysis/collect.py`) respecte strictement :

* le fichier `robots.txt` de **chaque domaine sollicité**, lu avant toute requête ;
* l'absence totale d'authentification, de cookie personnel ou de session privée ;
* l'absence de tout contournement de CAPTCHA, de protection anti-bot ou de limitation d'API ;
* une seule requête par voie autorisée, avec délai entre les sources ;
* l'absence de recherche ou de conservation de données privées.

Lorsqu'une plateforme empêche la récupération, la limite est **documentée**, jamais contournée.

---

## Déploiement sur Vercel

1. Ajouter ou mettre à jour les données dans `data/`.
2. `python analysis/run_analysis.py`
3. Vérifier les JSON produits dans `public/data/`.
4. `git add . && git commit && git push`
5. Vercel redéploie automatiquement le tableau de bord.

Aucun serveur Python n'est nécessaire en production : les résultats sont des fichiers statiques.

---

## Structure du dépôt

```
social-polarization-MVP/
├── analysis/          # pipeline Python
├── data/              # sources, modèle d'import, jeu de démonstration
├── docs/              # documentation française
├── public/data/       # résultats JSON consommés par le tableau de bord
├── src/               # tableau de bord Next.js
├── tests/             # tests pytest
├── requirements.txt
└── package.json
```

---

## Documentation

* [Méthodologie](docs/METHODOLOGIE.md)
* [Données et schéma](docs/DONNEES.md)
* [Collecte des données](docs/COLLECTE_DES_DONNEES.md)
* [Résultats](docs/RESULTATS.md)
* [Limites](docs/LIMITES.md)
* [Rapport complet du MVP](docs/RAPPORT_MVP.md)

---

*Préparation, conception et programmation : Dr. Okba Ben Atia*
