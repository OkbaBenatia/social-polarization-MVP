# Collecte des données

> Préparation, conception et programmation : **Dr. Okba Ben Atia**

Ce document rend compte, source par source, de ce qui a **réellement** pu être récupéré, de ce
qui ne l'a pas été, et des raisons techniques et éthiques correspondantes.

---

## 1. Cadre éthique et technique

La tentative de collecte est réalisée par `analysis/collect.py`. Elle applique les règles
suivantes, sans exception :

| Règle | Mise en œuvre |
|-------|---------------|
| Respect du protocole d'exclusion | Le fichier `robots.txt` de **chaque domaine sollicité** est lu **avant** toute requête de contenu. S'il interdit l'accès, ou s'il ne peut pas être lu, aucune requête n'est émise. |
| Aucune authentification | Aucun identifiant, aucun mot de passe, aucun jeton d'API privé. |
| Aucun cookie personnel | Aucune session utilisateur n'est réutilisée. |
| Aucun contournement | Ni CAPTCHA, ni protection anti-bot, ni limitation d'API ne sont contournés. Un mur d'authentification détecté est documenté, jamais franchi. |
| Aucun scraping agressif | Une seule requête par voie autorisée, avec délai entre les sources, et un agent utilisateur explicite. |
| Aucune donnée privée | Seules les métadonnées publiques (`og:title`, `og:description`, `og:type`, `og:url`, `<title>`) sont extraites. Aucune donnée personnelle n'est recherchée ni conservée. |

Agent utilisateur déclaré :

```
social-polarization-MVP/0.1 (recherche academique ; collecte de metadonnees publiques)
```

Pour chaque source, **deux voies d'accès** sont évaluées :

1. la **page publique** de la publication (lecture des balises Open Graph) ;
2. le **point d'accès oEmbed officiel** de la plateforme, lorsqu'il existe.

Chaque voie est confrontée au `robots.txt` de son propre domaine. Le refus est enregistré comme
un **résultat de l'étude**, jamais contourné.

Le rapport complet, horodaté, est écrit dans `data/collection_report.json` et lu ensuite par le
pipeline pour déterminer le statut de chaque source.

---

## 2. Statuts de collecte

| Statut | Signification |
|--------|---------------|
| **Données disponibles** | Des interactions réelles ont été importées au format normalisé pour cette source. |
| **Accès partiel** | Seules des métadonnées publiques ont pu être lues ; aucune interaction n'a été récupérée. |
| **Import manuel requis** | La collecte automatique n'a rien produit d'exploitable. Les données doivent être fournies via `data/import_template.csv`. |
| **Données de démonstration** | Les interactions rattachées à cette source proviennent du jeu synthétique, et non de la plateforme. |

Un statut n'est jamais renseigné à la main : il est **déduit** du rapport de collecte et du
contenu réellement importé (`analysis/load_sources.py`).

---

## 3. Résultat de la tentative de collecte

Exécution du **24 août 2026**, depuis une machine disposant d'un **accès réseau sortant complet
et vérifié** (aucun mandataire bloquant, `robots.txt` des trois plateformes lus avec succès).
Rapport : `data/collection_report.json`.

**Bilan : 14 voies d'accès évaluées, 14 refusées par `robots.txt`, 0 interaction récupérée sur
7 sources.**

| Source | Plateforme | URL | Voies évaluées | Requêtes émises | Interactions récupérées | Import manuel |
|--------|-----------|-----|----------------|-----------------|------------------------|---------------|
| `facebook_001` | Facebook | https://www.facebook.com/share/v/18hGjKiFVK/ | 2 | 0 | **0** | **oui** |
| `facebook_002` | Facebook | https://www.facebook.com/share/p/1HYJ6PKM2Q/ | 2 | 0 | **0** | **oui** |
| `facebook_003` | Facebook | https://www.facebook.com/share/v/1GCZzavgcV/ | 2 | 0 | **0** | **oui** |
| `facebook_004` | Facebook | https://www.facebook.com/share/p/1F5HSSqfkM/ | 2 | 0 | **0** | **oui** |
| `facebook_005` | Facebook | https://www.facebook.com/share/p/18GdU39RoV/ | 2 | 0 | **0** | **oui** |
| `x_001` | X | https://x.com/i/status/2087872720012796385 | 2 | 0 | **0** | **oui** |
| `instagram_001` | Instagram | https://www.instagram.com/reel/DbtVlHYABVK/ | 2 | 0 | **0** | **oui** |

### 3.1 Cause constatée : refus explicite du protocole d'exclusion

Contrairement à une indisponibilité réseau, le refus constaté est **une décision explicite des
plateformes**, vérifiable et reproductible. Directives applicables à un agent générique, lues
le 24 août 2026 :

| Domaine sollicité | Voie concernée | Directive `robots.txt` |
|-------------------|----------------|------------------------|
| `www.facebook.com` | page publique des 5 publications Facebook | `User-agent: *` → `Disallow: /` |
| `graph.facebook.com` | oEmbed officiel Facebook et Instagram | `User-agent: *` → `Disallow: /` |
| `www.instagram.com` | page publique du reel | `User-agent: *` → `Disallow: /` |
| `x.com` | page publique de la publication X | `User-agent: *` → `Disallow: /` |
| `publish.x.com` | oEmbed officiel X | `User-agent: *` → `Disallow: /oembed` |

L'en-tête du `robots.txt` de Meta est explicite :

> « Collection of data on Facebook through automated means is prohibited unless you have express
> written permission from Facebook. »

Conformément au cadre retenu, **aucune requête de contenu n'a été émise** vers ces voies. Les
sept sources ont donc été marquées comme nécessitant un import manuel.

### 3.2 Vérification manuelle de faisabilité (hors pipeline)

Afin de documenter précisément ce qui *serait* accessible en cas d'autorisation, une
vérification manuelle ponctuelle a été effectuée pendant l'étude de faisabilité, **avant** que le
verdict `robots.txt` de chaque point d'accès oEmbed ne soit établi. Elle n'a pas été reconduite
et n'alimente aucun résultat.

| Point d'accès | Réponse | Champs réellement exposés |
|---------------|---------|---------------------------|
| oEmbed X (`publish.x.com/oembed`) | HTTP 200 | auteur, texte intégral de la publication, date, hashtags, présence d'un média. **Aucun** commentaire, réponse ou repost. |
| oEmbed Instagram (`graph.facebook.com/instagram_oembed`) | HTTP 200 | conteneur d'intégration générique uniquement — **ni légende, ni auteur, ni commentaire**. |
| oEmbed Facebook (`graph.facebook.com/oembed_post`) | HTTP 400 | aucun : un jeton d'application Meta approuvé est exigé. |

Trois conclusions en découlent :

1. **Aucun point d'accès officiel n'expose les interactions entre utilisateurs**, qui
   constituent la matière première de cette étude. Au mieux, X expose le texte d'une
   publication isolée.
2. Ces voies étant **interdites par `robots.txt`**, elles sont exclues du pipeline. Aucune
   donnée issue de cette vérification n'est intégrée au corpus, ni republiée dans ce dépôt.
3. Le contenu de `x_001` est **transcriptible manuellement** par un chercheur consultant
   normalement la page : c'est la voie d'acquisition légitime retenue (section 5).

### 3.3 Cause structurelle, indépendante de l'environnement

Même avec une autorisation d'accès, la collecte automatisée des **interactions** resterait hors
de portée d'un MVP :

* **Facebook** — les publications partagées via `facebook.com/share/…` redirigent vers une page
  qui exige une session authentifiée pour afficher les commentaires et les réponses. Leur
  récupération légitime suppose l'API Graph avec une application approuvée.
* **X** — l'accès programmatique aux réponses, reposts et citations passe exclusivement par
  l'API X, soumise à souscription. Le point d'accès oEmbed ne renvoie qu'une publication isolée.
* **Instagram** — la légende complète et les commentaires nécessitent une session ou l'API
  Instagram Graph, réservée aux comptes professionnels et aux applications approuvées.

En résumé : **le texte d'une publication peut parfois être lu publiquement, mais les interactions
entre utilisateurs ne le sont sur aucune des trois plateformes.**

---

## 4. Données réellement accessibles et données manquantes

Synthèse par source. « Accessible » signifie : exposé publiquement par la plateforme.
« Récupéré » signifie : **effectivement obtenu par le pipeline**, dans le respect du cadre.

| Source | Données accessibles publiquement | Données récupérées | Données manquantes | Import manuel |
|--------|----------------------------------|--------------------|--------------------|---------------|
| `facebook_001` … `facebook_005` | aucune sans session authentifiée | **aucune** | texte, commentaires, réponses, mentions, partages, relations, horodatages | **oui** |
| `x_001` | texte, auteur, date, hashtags (via oEmbed, voie interdite par `robots.txt`) | **aucune** | commentaires, réponses, mentions, reposts, relations, horodatages | **oui** |
| `instagram_001` | aucune donnée de contenu (conteneur d'intégration seul) | **aucune** | texte, commentaires, réponses, mentions, partages, relations, horodatages | **oui** |

Détail par type de donnée :

| Donnée souhaitée | Facebook | X | Instagram | Commentaire |
|------------------|----------|---|-----------|-------------|
| Texte de la publication | non | oEmbed (voie interdite) | non | Seul X l'expose hors session. |
| Légende | non | — | non | |
| Date | non | oEmbed (voie interdite) | non | |
| Commentaires | non | non | non | Jamais exposés sans authentification. |
| Réponses | non | non | non | |
| Mentions | non | non | non | |
| Reposts / citations | — | API souscrite | — | |
| Partages | non | — | non | |
| Interactions entre utilisateurs | **non** | **non** | **non** | Cœur de l'étude, non accessible. |

**Les 7 sources nécessitent donc un import manuel.**

---

## 5. Procédure d'import manuel

L'import manuel constitue la voie d'acquisition retenue pour ce MVP.

1. **Rassembler les données** par un moyen légitime : export de données fourni par la
   plateforme, accès via une API autorisée, ou saisie manuelle à partir de contenus publics
   consultés normalement.
2. **Les mettre au format normalisé**, en repartant de `data/import_template.csv` :

   ```csv
   platform,source_id,post_id,interaction_id,source_user,target_user,interaction_type,text,timestamp,parent_id,url
   ```

   * `source_id` doit correspondre à un identifiant déclaré dans `data/sources.json` ;
   * `parent_id` conditionne la qualité de l'analyse de propagation : il doit pointer vers le
     `post_id` pour un commentaire, et vers l'`interaction_id` du parent pour une réponse ;
   * les identifiants d'utilisateurs peuvent rester bruts : ils sont pseudonymisés par le
     pipeline avant toute analyse.
3. **Déposer le fichier** (CSV ou JSON) dans `data/imported/`.
4. **Relancer l'analyse** :

   ```bash
   python analysis/run_analysis.py
   ```

Dès qu'un fichier est présent dans `data/imported/`, le jeu de démonstration est ignoré : le
corpus est déclaré réel, l'avertissement « données synthétiques » disparaît, les statuts des
sources concernées passent à « Données disponibles », et aucun extrait de contenu n'est publié
dans `public/data/`.

Cette bascule a été vérifiée sur un extrait de 47 interactions rattachées à `facebook_001` :
le corpus a bien été déclaré réel, seule cette source est passée au statut « Données
disponibles », les six autres sont restées en « Import manuel requis », et aucun extrait n'a été
publié.

---

## 6. Limites de la collecte

### 6.1 Limites techniques

* Les trois plateformes interdisent explicitement la collecte automatisée par `robots.txt`.
* Aucune d'entre elles n'expose publiquement les interactions entre utilisateurs.
* L'accès aux API officielles suppose une souscription, une application approuvée et, pour
  Facebook et Instagram, une revue de la plateforme — hors du périmètre d'un MVP.
* Les URLs de partage (`/share/…`, `?igsh=…`) sont des redirections opaques : elles ne
  garantissent ni la stabilité de l'identifiant, ni la disponibilité future du contenu.
* Un contenu supprimé, rendu privé ou géo-restreint devient inaccessible sans préavis.

### 6.2 Limites éthiques

* La collecte de commentaires nominatifs relève de données à caractère personnel : elle exige
  une base légale, une information des personnes concernées et une minimisation des données.
  Le projet y répond par la pseudonymisation systématique et par la non-publication des
  contenus réels.
* Les conditions d'utilisation des plateformes interdisent la collecte automatisée non
  autorisée. Le projet s'y conforme : aucune protection n'est contournée.
* L'analyse porte sur des **contenus et des structures collectives**, jamais sur la
  personnalité des individus. Aucun profilage individuel n'est réalisé.
* Aucun attribut sensible n'est inféré : ni religion, ni origine, ni ethnie, ni orientation
  politique.

### 6.3 Conséquence sur les résultats actuels

Aucune donnée réelle n'ayant pu être récupérée à ce jour, les résultats publiés dans le tableau
de bord proviennent du **jeu de démonstration synthétique**. Ils valident le fonctionnement du
dispositif et **ne constituent pas des résultats empiriques**. Cette nature est signalée sur
chaque page du tableau de bord et dans chacun des neuf fichiers JSON produits. L'indicateur
« Sources analysées » affiche en conséquence **0 / 7**.

---

## 7. Reproduire la tentative de collecte

```bash
python analysis/collect.py
```

Le rapport écrit dans `data/collection_report.json` contient, pour chaque source : l'horodatage
de la tentative, la liste des voies évaluées avec le verdict `robots.txt` de chacune, le fait
qu'une requête ait été émise ou non, le code HTTP obtenu le cas échéant, les métadonnées
publiques éventuellement lues, la détection d'un mur d'authentification, les données récupérées,
les données manquantes, la nécessité d'un import manuel et la liste des limites constatées.

Ce rapport est ensuite lu par `analysis/run_analysis.py`, qui en déduit le statut affiché pour
chaque source dans le tableau de bord.

---

*Préparation, conception et programmation : Dr. Okba Ben Atia*
