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
| Respect du protocole d'exclusion | Le fichier `robots.txt` de chaque plateforme est lu **avant** toute requête de contenu. S'il interdit l'accès, ou s'il ne peut pas être lu, aucune requête de contenu n'est effectuée. |
| Aucune authentification | Aucun identifiant, aucun mot de passe, aucun jeton d'API privé. |
| Aucun cookie personnel | Aucune session utilisateur n'est réutilisée. |
| Aucun contournement | Ni CAPTCHA, ni protection anti-bot, ni limitation d'API ne sont contournés. Un mur d'authentification détecté est documenté, jamais franchi. |
| Aucun scraping agressif | Une seule requête par URL, avec un délai de deux secondes entre les requêtes, et un agent utilisateur explicite. |
| Aucune donnée privée | Seules les métadonnées publiques (`og:title`, `og:description`, `og:type`, `og:url`, `<title>`) sont extraites. Aucune donnée personnelle n'est recherchée ni conservée. |

Agent utilisateur déclaré :

```
social-polarization-MVP/0.1 (recherche academique ; collecte de metadonnees publiques)
```

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

Exécution du 19 août 2026 (rapport : `data/collection_report.json`).

| Source | Plateforme | URL | Réponse HTTP | Métadonnées publiques | Interactions récupérées |
|--------|-----------|-----|--------------|----------------------|------------------------|
| `facebook_001` | Facebook | https://www.facebook.com/share/v/18hGjKiFVK/ | aucune réponse obtenue | aucune | **0** |
| `facebook_002` | Facebook | https://www.facebook.com/share/p/1HYJ6PKM2Q/ | aucune réponse obtenue | aucune | **0** |
| `facebook_003` | Facebook | https://www.facebook.com/share/v/1GCZzavgcV/ | aucune réponse obtenue | aucune | **0** |
| `facebook_004` | Facebook | https://www.facebook.com/share/p/1F5HSSqfkM/ | aucune réponse obtenue | aucune | **0** |
| `facebook_005` | Facebook | https://www.facebook.com/share/p/18GdU39RoV/ | aucune réponse obtenue | aucune | **0** |
| `x_001` | X | https://x.com/i/status/2087872720012796385 | aucune réponse obtenue | aucune | **0** |
| `instagram_001` | Instagram | https://www.instagram.com/reel/DbtVlHYABVK/ | aucune réponse obtenue | aucune | **0** |

**Bilan : 0 interaction récupérée automatiquement sur 7 sources.**

### 3.1 Cause immédiate constatée

Pour les sept URLs, la lecture préalable de `robots.txt` a échoué avec l'erreur réseau
suivante :

```
URLError : <urlopen error Tunnel connection failed: 403 Forbidden>
```

L'environnement d'exécution utilisé pour cette exécution refuse l'accès sortant vers
`facebook.com`, `x.com` et `instagram.com` (politique réseau du mandataire). Conformément au
cadre retenu, **cette restriction n'a pas été contournée** : aucune requête de contenu n'a été
émise, et la source a été marquée comme nécessitant un import manuel.

Ce comportement est volontairement conservateur : lorsque le protocole d'exclusion ne peut pas
être vérifié, la collecte n'est pas tentée.

### 3.2 Cause structurelle, indépendante de l'environnement

Même avec un accès réseau complet, la collecte automatisée des **interactions** resterait
impossible dans le cadre éthique retenu :

* **Facebook** — les publications partagées via `facebook.com/share/…` redirigent vers une page
  qui exige une session authentifiée pour afficher les commentaires et les réponses. Les
  commentaires ne sont pas exposés dans le HTML public. Leur récupération légitime suppose
  l'API Graph avec une application approuvée et les autorisations correspondantes.
* **X** — l'accès programmatique aux publications, réponses, reposts et citations passe
  exclusivement par l'API X, soumise à souscription. Les pages `x.com/i/status/…` servies sans
  authentification ne contiennent pas le fil de discussion.
* **Instagram** — les pages `instagram.com/reel/…` exposent au mieux quelques métadonnées Open
  Graph ; la légende complète et les commentaires nécessitent une session ou l'API Instagram
  Graph, réservée aux comptes professionnels et à des applications approuvées.

En résumé : **les métadonnées d'une publication peuvent parfois être lues publiquement, mais les
interactions entre utilisateurs — qui constituent la matière première de cette étude — ne le
sont sur aucune des trois plateformes.**

---

## 4. Données réellement accessibles et données manquantes

| Donnée souhaitée | Facebook | X | Instagram | Commentaire |
|------------------|----------|---|-----------|-------------|
| Texte de la publication | métadonnées seulement, avec session | API | métadonnées seulement | Souvent tronqué dans `og:description`. |
| Légende | non | API | non | |
| Date | non | API | non | Rarement exposée publiquement. |
| Commentaires | non | non | non | Jamais exposés sans authentification. |
| Réponses | non | non | non | |
| Mentions | non | non | non | |
| Reposts / retweets | non | API | — | |
| Citations | — | API | — | |
| Partages | non | — | non | |
| Interactions entre utilisateurs | **non** | **non** | **non** | Cœur de l'étude, non accessible. |

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

* Aucune des trois plateformes n'expose publiquement les interactions entre utilisateurs.
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
chaque page du tableau de bord et dans chacun des neuf fichiers JSON produits.

---

## 7. Reproduire la tentative de collecte

```bash
python analysis/collect.py
```

Le rapport écrit dans `data/collection_report.json` contient, pour chaque source : l'horodatage
de la tentative, la méthode, le résultat de la vérification `robots.txt`, le code HTTP obtenu,
les métadonnées publiques éventuellement lues, la détection d'un mur d'authentification, le
nombre d'interactions récupérées et la liste des limites constatées.

Ce rapport est ensuite lu par `analysis/run_analysis.py`, qui en déduit le statut affiché pour
chaque source.

---

*Préparation, conception et programmation : Dr. Okba Ben Atia*
