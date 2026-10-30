# CLAUDE.md

Guide de travail pour Claude Code sur ce dépôt. La présentation générale se trouve dans
`README.md` et la méthode dans `docs/` ; ce fichier ne reprend que ce qu'il faut savoir pour
modifier le code sans casser la chaîne ni les garde-fous scientifiques.

## Vue d'ensemble

MVP académique (Dr. Okba Ben Atia) : polarisation et propagation du discours de haine sur
7 publications Facebook / X / Instagram déclarées dans `data/sources.json`.

```
data/*.csv ──► pipeline Python hors ligne (analysis/) ──► public/data/*.json ──► Next.js (src/) ──► Vercel
```

* Tout le calcul est fait **hors ligne** en Python. Le tableau de bord ne fait que lire les
  JSON de `public/data/` (côté serveur, via `src/lib/data.ts`). Pas de base de données, pas de
  backend Python en production.
* Les JSON de `public/data/` sont **versionnés** : c'est ce que Vercel publie.

## Commandes

```bash
# Python — utiliser un venv : avec le setuptools système (Debian), python-louvain ne s'installe pas.
python3 -m venv .venv && .venv/bin/pip install -U pip setuptools wheel
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest                          # 125 tests, ~3 s (pytest.ini : pythonpath = analysis tests)
.venv/bin/python -m pytest tests/test_preprocess.py -k nom_du_test

# Pipeline — corpus actuellement publié (346 interactions ScrapeCreators réelles)
.venv/bin/python analysis/run_analysis.py --input data/real_interactions.csv
# Sortie ailleurs que public/data (pour comparer sans toucher aux fichiers publiés)
.venv/bin/python analysis/run_analysis.py --input data/real_interactions.csv --sortie /chemin/temp

# Tableau de bord
npm install
npm run dev            # http://localhost:3000
npm run lint
npx tsc --noEmit       # vérification de types (npm run build la fait aussi)
npm run build
```

Avant de committer : `pytest`, `npm run lint` et `npx tsc --noEmit` doivent passer.

## Les deux modes du pipeline

`analysis/run_analysis.py` charge les données de deux façons différentes :

1. **`--input <fichier>` (mode « empirique », celui de la publication actuelle).** Chaque ligne
   doit porter une provenance réelle (`analysis/provenance.py` : `official_api`, `public_page`,
   `manual_verified`, `scrapecreators_public`). Un fichier vide ou une ligne `synthetic_demo`
   provoque un refus.
2. **Sans `--input`.** Le pipeline lit `data/imported/*` s'il y a des fichiers, sinon le jeu
   synthétique `data/sample_interactions.csv`, signalé sur chaque page du tableau de bord.

Le README décrit encore l'état d'août 2026 (« données de démonstration »). Les JSON publiés
sont désormais produits en mode `--input data/real_interactions.csv`
(`overview.json → jeu_de_donnees.mode = "empirique"`). Si on relance le pipeline sans
`--input`, on republie le corpus synthétique : à ne faire que volontairement.

### Chaîne de collecte ScrapeCreators

```
analysis/collect_scrapecreators.py   # appels API payants ; SCRAPECREATORS_API_KEY ; cache brut dans data/raw/ (ignoré par git)
analysis/rebuild_from_raw.py         # reconstruit data/scrapecreators/*.csv depuis le cache, sans réseau
analysis/build_real_dataset.py       # agrège -> data/real_interactions.csv (refuse toute ligne synthétique)
analysis/run_analysis.py --input data/real_interactions.csv
```

* Ne jamais lancer `collect_scrapecreators.py` sans demande explicite : chaque appel consomme
  des crédits. Pour reconstruire les CSV, utiliser `rebuild_from_raw.py`.
* X : ScrapeCreators n'expose pas les réponses. Seul le post est enregistré
  (`replies_supported = false`), et rien n'est fabriqué pour compenser.
* `analysis/collect.py` correspond à l'ancienne collecte publique : elle respecte robots.txt,
  et toutes ses voies ont été refusées.

### Reproductibilité et pseudonymisation

* Les identifiants d'utilisateurs sont pseudonymisés par HMAC-SHA256. Le sel vient de
  `ANONYMIZATION_SALT` ou, à défaut, de `data/private/sel_anonymisation.txt`, créé au premier
  lancement. `data/private/` est ignoré par git et ne doit **jamais** se retrouver dans
  `public/`.
* Sans le sel d'origine, relancer le pipeline change tous les `usr_…` / « Utilisateur NNN »
  ainsi que `genere_le` dans les 9 JSON. Les indicateurs, eux, restent identiques. Ne pas
  committer ces changements de bruit quand on ne voulait modifier que le code. Pour vérifier
  un changement, générer dans un répertoire temporaire (`--sortie`) et comparer.

## Organisation du code

* `analysis/` : un module par étape (`preprocess`, `network_analysis`, `community_detection`,
  `sentiment_analysis`, `emotion_analysis`, `hate_speech_analysis`, `propagation_analysis`…),
  orchestrés par `run_analysis.py`. Les scripts s'importent entre eux par
  `sys.path.insert(0, …)` suivi de `import module  # noqa: E402`, sans package. Les erreurs
  métier passent par des exceptions dédiées (`ErreurDonnees`, `ErreurSources`, `ErreurQualite`,
  `ErreurPipeline`), interceptées dans `main()`.
* `src/app/<page>/page.tsx` : une route par page du tableau de bord (vue d'ensemble, sources,
  réseau, communautés, contenu, sentiments, discours-haineux, propagation, méthodologie).
* `src/lib/types.ts` décrit la forme des JSON. Si le pipeline modifie un JSON, mettre à jour
  ces types **et** `tests/test_pipeline_json.py`.
* `src/lib/data.ts` : `lireResultats` renvoie `null` quand un fichier manque ou est illisible,
  et la page affiche alors `EtatVide` au lieu de planter.
* `src/components/ui/` contient les briques d'interface, `src/components/graphiques/` les
  graphiques Recharts, `ReseauCytoscape.tsx` le graphe. Les couleurs sont dans
  `src/lib/palette.ts` et `src/lib/theme.ts`, avec un mode clair et un mode sombre.
* `scripts/` sert aux livrables (`capture_dashboard.py` pour les captures Playwright,
  `generate_report.py` pour le rapport .docx tiré des JSON).
* `.claude/skills/*` sont des liens symboliques vers `.agents/skills/*` (skills ScrapeCreators
  et recherche sociale).

## Conventions

* **Tout est en français** : identifiants Python et TypeScript (`charger_jeu_de_donnees`,
  `lireOverview`, `KpiCarte`), docstrings, commentaires, messages d'erreur, interface,
  documentation.
* Les docstrings de module se terminent par
  `Préparation, conception et programmation : Dr. Okba Ben Atia`.
* Aucune statistique n'est écrite en dur dans React ou dans le rapport : tout chiffre provient
  de `public/data/*.json`.
* Dépendances Python volontairement minimales (voir `requirements.txt`). En ajouter une
  seulement si c'est nécessaire.

## Garde-fous scientifiques et éthiques (non négociables)

* Distinguer polarisation, sentiment négatif, colère, toxicité et discours haineux. On ne
  fusionne pas ces dimensions.
* Les communautés portent des noms neutres (« Communauté 1 »…). Jamais d'étiquette
  idéologique automatique.
* Écrire « contenu classifié comme potentiellement haineux », jamais « utilisateur haineux ».
* Les classifieurs sont heuristiques et indicatifs. N'annoncer **aucune** précision, aucun
  rappel, aucun F1.
* N'inférer aucun attribut sensible : religion, origine, ethnie, orientation politique.
* Ne jamais mélanger données réelles et synthétiques sans le signaler, ne jamais fabriquer de
  données, ne jamais présenter une source comme analysée si ses données n'ont pas été
  réellement obtenues.
* Collecte : pas d'authentification, pas de cookies personnels, pas de contournement de
  CAPTCHA ou d'anti-bot. Une limite rencontrée est documentée, pas contournée.
* Aucun secret (clé API, sel) dans le code, les CSV, les JSON, les journaux ou la
  documentation.
