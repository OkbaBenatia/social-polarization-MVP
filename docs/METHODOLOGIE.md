# Méthodologie

> Préparation, conception et programmation : **Dr. Okba Ben Atia**

Ce document décrit la chaîne de traitement complète, les choix méthodologiques retenus et leurs
justifications.

---

## 1. Objectif

L'étude vise à décrire, sur un corpus d'interactions publiques, la structure des échanges autour
de sujets sensibles : arabisation, religion, immigration, identité, et questions sociales et
politiques connexes.

Trois objectifs sont poursuivis :

1. reconstituer un réseau d'interactions entre utilisateurs à partir de données publiques ou
   importées ;
2. y détecter des communautés et mesurer leur degré de séparation structurelle ;
3. caractériser les contenus échangés — vocabulaire, sentiment, colère et soutien, toxicité —
   et leur propagation.

Il s'agit d'un MVP académique fonctionnel, et non d'une plateforme de traitement à grande
échelle. L'ensemble des calculs est effectué hors ligne en Python ; le tableau de bord ne fait
que restituer des résultats déjà produits.

---

## 2. Sources

Les sources initiales sont sept publications réelles — cinq sur Facebook, une sur X, une sur
Instagram — déclarées dans `data/sources.json` avec leur plateforme, leur identifiant et leur
URL.

Aucune source n'est présentée comme analysée tant que ses données n'ont pas été réellement
récupérées ou importées. Quatre statuts sont possibles : **Données disponibles**, **Accès
partiel**, **Import manuel requis**, **Données de démonstration**. Ce statut est déduit du
rapport de collecte et du contenu effectivement importé, jamais renseigné manuellement.

Voir [`docs/COLLECTE_DES_DONNEES.md`](COLLECTE_DES_DONNEES.md).

---

## 3. Collecte

`analysis/collect.py` tente une lecture publique des URLs déclarées, limitée aux métadonnées
Open Graph exposées sans authentification.

Règles appliquées sans exception :

* lecture préalable de `robots.txt` ; si l'accès est interdit ou si le fichier ne peut pas être
  lu, **aucune requête de contenu n'est émise** ;
* aucune authentification, aucun cookie personnel, aucune session privée ;
* aucun contournement de CAPTCHA, de protection anti-bot ou de limitation d'API ;
* une seule requête par URL, avec un délai de deux secondes entre les requêtes ;
* aucune donnée privée n'est recherchée ni conservée.

Lorsque la plateforme empêche la récupération, la limite est **documentée**, jamais contournée.
Le projet bascule alors sur un import manuel au format normalisé
(`data/import_template.csv`). Le pipeline analyse rigoureusement les mêmes données, quelle que
soit leur provenance : collecte publique, export de plateforme, CSV manuel ou JSON.

---

## 4. Anonymisation

Tous les identifiants d'utilisateurs sont pseudonymisés **avant toute analyse** :

1. un sel est lu depuis `ANONYMIZATION_SALT`, ou généré une fois et conservé localement dans
   `data/private/` ;
2. chaque identifiant devient `usr_` + douze caractères de `HMAC-SHA256(sel, identifiant)` ;
3. une étiquette d'affichage neutre est attribuée de façon déterministe : « Utilisateur 001 »,
   « Utilisateur 002 »…

La table de correspondance reste strictement locale et n'est jamais publiée dans `public/`.

Aucun attribut sensible n'est inféré : ni religion, ni origine, ni ethnie, ni orientation
politique, ni opinion personnelle. L'analyse porte sur des contenus et des structures
collectives, jamais sur la personnalité des individus.

Les extraits de contenu ne sont publiés dans les résultats **que si le corpus analysé est
synthétique** : aucun contenu réel d'utilisateur n'est republié.

---

## 5. Prétraitement

Le texte brut (`raw_text`) est conservé, et une version nettoyée est produite (`clean_text`).

Le prétraitement prend en charge le français, l'arabe et les textes mixtes :

* normalisation Unicode (NFKC) ;
* suppression des URLs et des mentions, extraites séparément ;
* suppression des diacritiques arabes (tashkeel) et du tatweel ;
* harmonisation des formes de l'alef, du ya, du waw hamzé et du ta marbuta ;
* réduction des répétitions de caractères (« trooop » → « troop ») ;
* passage en minuscules et suppression de la ponctuation résiduelle.

Les **hashtags sont conservés** lorsqu'ils portent une valeur analytique : le croisillon est
retiré mais le terme est maintenu dans le corpus, et la liste des hashtags est extraite
séparément. Mentions, URLs et emojis sont également extraits séparément.

La langue de chaque message est estimée à partir des systèmes d'écriture présents : `fr`, `ar`,
`mixte` ou `indetermine`.

Deux flux de jetons sont produits :

* `jetons` — jetons complets, mots vides conservés, utilisés par les classifieurs qui ont besoin
  des marques de négation et des adverbes d'intensité ;
* `jetons_lexicaux` — jetons après suppression des mots vides français et arabes, utilisés pour
  l'analyse lexicale.

Les élisions françaises sont découpées (« l'école » → « l » + « école »), ce qui isole le terme
porteur de sens tout en préservant la négation (« n'est pas »).

La darija écrite en caractères latins n'est pas traitée de manière spécifique : ce choix est
assumé pour ne pas complexifier inutilement le dispositif, et documenté comme une limite.

---

## 6. Réseau

Le réseau est un graphe **orienté et pondéré** :

* **nœud** : utilisateur pseudonymisé ;
* **lien** : interaction dirigée de l'auteur vers l'utilisateur visé ;
* **poids** : nombre d'interactions agrégées entre deux utilisateurs.

Les types produisant un lien sont `comment`, `reply`, `mention`, `share`, `repost` et `quote`.
Les publications (`post`) ne créent pas de lien mais alimentent le compte de messages de leur
auteur. Les auto-interactions (auteur = cible) sont exclues.

Mesures calculées : nombre de nœuds et de liens, poids total, densité, degré moyen, degrés
entrant et sortant, réciprocité, composantes faiblement connexes et taille de la composante
principale.

Centralités par nœud : degré, degré entrant, degré sortant, poids entrant et sortant, centralité
de degré, centralités entrante et sortante, centralité d'intermédiarité. Cette dernière est
calculée exactement jusqu'à 800 nœuds ; au-delà, elle est estimée par échantillonnage
(200 pivots, graine fixe), afin de rester exécutable sur un ordinateur standard.

Le fichier exporté vers le tableau de bord est borné à **1 000 nœuds** (`MAX_NETWORK_NODES`),
retenus par degré décroissant, afin de préserver la fluidité du navigateur. Lorsque cette borne
s'applique, le tableau de bord l'indique explicitement.

---

## 7. Communautés

La détection utilise l'algorithme de **Louvain** (Blondel et al., 2008), appliqué à la
projection non orientée et pondérée du réseau : les poids des deux sens sont additionnés.
L'implémentation `python-louvain` est utilisée en priorité ; à défaut, celle de NetworkX prend
le relais. Une graine fixe (42) garantit la reproductibilité.

Les identifiants de communauté sont renumérotés de façon stable, par taille décroissante.

Les communautés ne reçoivent que des **noms neutres** : « Communauté 1 », « Communauté 2 »…
Aucune étiquette idéologique — « pro-Islam », « anti-immigration », « extrémiste », « haineux »
ou équivalent — n'est générée automatiquement. Ce choix n'est pas cosmétique : une communauté
est une structure d'interaction, non un groupe d'opinion. Deux utilisateurs peuvent être proches
dans le graphe parce qu'ils s'affrontent régulièrement. **L'interprétation idéologique demeure
une tâche humaine.**

Sont calculés, par communauté : nombre d'utilisateurs, nombre de messages, liens et interactions
internes, liens et interactions externes, part d'interactions internes, ainsi que la matrice
orientée des interactions entre communautés.

Leiden n'a pas été retenu : son installation (`igraph` + `leidenalg`) ajouterait des dépendances
compilées sans bénéfice décisif à cette échelle.

---

## 8. Modularité

La modularité de Newman mesure l'écart entre la densité des liens observés à l'intérieur des
communautés et celle attendue dans un graphe aléatoire de même distribution de degrés. Elle est
calculée sur la projection pondérée, avec la partition retenue
(`networkx.community.modularity`).

Elle est comprise entre −0,5 et 1. Une valeur élevée traduit une structure communautaire nette :
les échanges se concentrent à l'intérieur des groupes.

---

## 9. Polarisation

La polarisation structurelle est décrite par des indicateurs **simples, transparents et
vérifiables** :

| Indicateur | Définition |
|------------|------------|
| Modularité | Voir section 8. |
| Interactions intra-communautés | Somme des poids des liens dont l'origine et la destination appartiennent à la même communauté. |
| Interactions inter-communautés | Somme des poids des liens reliant deux communautés différentes. |
| Ratio intra/inter | Rapport des deux quantités précédentes. Non défini si aucune interaction externe n'existe. |
| Part de liens internes | Interactions intra rapportées au total. |

Les valeurs numériques sont **toujours affichées**. Une lecture qualitative les accompagne :

| Modularité | Lecture indicative |
|------------|--------------------|
| < 0,30 | Polarisation faible |
| 0,30 ≤ *Q* < 0,50 | Polarisation modérée |
| ≥ 0,50 | Polarisation forte |

> **Ces seuils sont indicatifs.** Ils relèvent d'un usage conventionnel en analyse de réseaux et
> ne constituent pas une métrique validée de la polarisation. Ils sont accompagnés d'un
> avertissement explicite dans les résultats JSON et dans le tableau de bord. **Aucun « score
> scientifique » n'est fabriqué.**

Précaution majeure du projet :

> polarisation ≠ sentiment négatif ≠ colère ≠ toxicité ≠ discours haineux

Une modularité élevée indique une séparation structurelle des échanges, pas une hostilité — et
réciproquement.

---

## 10. Analyse lexicale

Pour chaque combinaison communauté × plateforme sont extraits :

* les **mots les plus fréquents**, après suppression des mots vides (listes françaises et arabes
  intégrées au projet, sans dépendance externe) ;
* les **bigrammes** de mots consécutifs ;
* les **termes caractéristiques** au sens de la pondération TF-IDF (scikit-learn), le score
  retourné étant la moyenne des poids sur les documents du sous-ensemble ;
* les **hashtags** principaux.

Les classements sont limités aux vingt premiers termes, ramenés à dix dans les fiches de
communauté. En deçà de trois documents, aucun TF-IDF n'est produit : une valeur calculée sur un
corpus trop réduit serait trompeuse.

Ces profils permettent la comparaison des champs lexicaux entre communautés (RQ3) et entre
plateformes (RQ8).

---

## 11. Sentiment

Trois catégories : **Positif**, **Neutre**, **Négatif**.

La classification est réalisée **hors ligne, en Python**, par un dispositif lexical à base de
règles couvrant le français et l'arabe :

* dictionnaires pondérés de termes positifs et négatifs ;
* gestion de la **négation** sur une fenêtre de trois jetons, avec inversion atténuée du poids ;
* gestion de l'**intensification** (« très », « trop », « جدا »…) ;
* décision par seuil : un score net inférieur à 1 en valeur absolue produit « Neutre ».

Une confiance indicative est calculée à partir de l'intensité du score rapportée au nombre de
marques lexicales détectées.

**Aucun modèle d'apprentissage automatique n'est chargé par le tableau de bord.**

### Choix méthodologique

Aucun modèle multilingue pré-entraîné n'a été retenu, faute de pouvoir en documenter honnêtement
les performances sur un corpus mêlant français, arabe standard et darija. Plutôt que d'annoncer
une précision invérifiable, l'analyse est présentée comme **indicative**, et l'architecture reste
**remplaçable** : la fonction `classer_texte()` de `analysis/sentiment_analysis.py` constitue le
point d'extension unique. La remplacer par un classifieur entraîné ne nécessite aucune
modification du reste du pipeline.

Le descriptif de la méthode — nom, version, langues couvertes, type, absence d'évaluation,
limites — est publié dans `sentiment.json` et affiché dans le tableau de bord.

> **Aucune mesure de précision, de rappel ou de F1 n'est annoncée : aucune évaluation sur corpus
> annoté n'a été réalisée.**

---

## 12. Colère et soutien

Trois catégories : **Colère**, **Soutien / approbation**, **Autre / neutre**.

Cette classification est **indépendante** de celle du sentiment. Elle combine :

* des dictionnaires lexicaux dédiés, en français et en arabe ;
* des marqueurs typographiques faibles, pondérés faiblement : points d'exclamation répétés,
  séquences de majuscules, quelques emojis explicites.

La décision retient la catégorie dominante à condition qu'elle dépasse un seuil et qu'elle ne
soit pas à égalité avec l'autre ; sinon « Autre / neutre » est retenu. Une confiance indicative
est dérivée de l'écart entre les deux scores.

L'objectif est de **comparer les communautés entre elles** (RQ5), non de caractériser des
personnes.

> Il s'agit d'une **classification automatique indicative du contenu**. Elle ne décrit pas
> l'état émotionnel réel d'une personne et ne doit jamais être interprétée comme tel.

---

## 13. Discours haineux

Trois catégories mutuellement exclusives :

| Catégorie | Critère |
|-----------|---------|
| **Non haineux** | Aucun signal détecté. |
| **Toxique / offensant** | Présence d'un ou plusieurs termes disqualifiant un interlocuteur (insulte, mépris). |
| **Potentiellement haineux** | **Co-occurrence** d'une désignation collective et d'une formulation d'exclusion, de rejet collectif ou de déshumanisation. |

La règle de co-occurrence est volontairement **conservatrice** : la seule mention d'un groupe ne
déclenche aucune classification, et une critique négative sans formulation d'exclusion reste
classée « Non haineux ». Ce choix limite les faux positifs sur des messages simplement
critiques.

Un **niveau de confiance** indicatif et la liste des signaux détectés sont enregistrés avec
chaque classification.

### Précautions terminologiques

* On ne parle **jamais** d'« utilisateur haineux », mais de « **contenu classifié comme
  potentiellement haineux** ».
* La classification signale un **signal lexical à vérifier manuellement** ; elle ne constitue
  pas une qualification juridique.
* Sentiment négatif, colère, toxicité et discours haineux restent quatre dimensions distinctes,
  jamais additionnées ni confondues.

> **Aucune performance n'est annoncée : aucune évaluation sur corpus annoté n'a été réalisée.**

---

## 14. Propagation

Les cascades sont reconstruites à partir du champ `parent_id` :

```
Publication
   ↓
Commentaire
   ↓
Réponse
   ↓
Partage / repost / citation
   ↓
Autre communauté
```

La profondeur d'une interaction est sa distance à la racine, obtenue en remontant la chaîne des
`parent_id`. Un parent absent est traité comme une racine ; un cycle éventuel est détecté et
neutralisé.

Pour chaque cascade sont calculés : la taille, la profondeur maximale, le nombre de
participants, la durée entre le premier et le dernier horodatage, les communautés atteintes, la
répartition par type d'interaction, ainsi que les proportions de contenus classés négatifs, en
colère, toxiques ou potentiellement haineux.

Les douze cascades les plus volumineuses sont exportées avec leur arbre détaillé (borné à
120 nœuds) pour la visualisation.

**Aucun modèle de diffusion** — épidémiologique, processus de Hawkes ou autre — n'est estimé :
l'analyse reste descriptive. La qualité de la reconstruction dépend directement de la présence
et de la cohérence du champ `parent_id` dans les données importées.

---

## 15. Limites

Les limites sont détaillées dans [`docs/LIMITES.md`](LIMITES.md). En résumé :

* **Collecte** — aucune des trois plateformes n'expose publiquement les interactions entre
  utilisateurs ; la collecte automatisée est donc impossible dans le cadre éthique retenu.
* **Classification** — les dispositifs de sentiment, de colère/soutien et de toxicité sont
  heuristiques, fondés sur des dictionnaires courts et non exhaustifs, et n'ont fait l'objet
  d'aucune évaluation. Aucune performance ne peut être annoncée.
* **Sémantique** — l'ironie, le sarcasme, l'implicite et les formulations codées échappent à la
  détection. Une citation ou une dénonciation d'un propos haineux peut être classée à tort.
* **Langue** — la darija en caractères latins n'est couverte que partiellement, ce qui introduit
  un biais linguistique.
* **Algorithmique** — Louvain est stochastique ; une graine fixe assure la reproductibilité,
  mais la partition obtenue n'est pas unique.
* **Interprétation** — les seuils de polarisation sont conventionnels et indicatifs ; aucune
  inférence causale n'est possible.
* **Corpus** — tant qu'aucune donnée réelle n'est importée, les résultats affichés proviennent
  d'un jeu synthétique et ne constituent pas des résultats empiriques.

---

## 16. Reproductibilité

```bash
pip install -r requirements.txt
python analysis/collect.py        # optionnel
python analysis/run_analysis.py
pytest
```

Sont fixés : la graine de Louvain (42), la graine de l'estimation d'intermédiarité (42), la
graine du générateur de données de démonstration (20260119), et le sel d'anonymisation
(variable `ANONYMIZATION_SALT` ou fichier local persistant).

Aucune statistique n'est écrite en dur dans l'interface : toutes les valeurs affichées
proviennent des fichiers `public/data/*.json`.

---

*Préparation, conception et programmation : Dr. Okba Ben Atia*
