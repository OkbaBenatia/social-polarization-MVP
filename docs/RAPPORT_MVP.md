# Étude de la polarisation et de la propagation du discours de haine sur les réseaux sociaux

## Analyse de réseaux, détection de communautés et analyse automatique du contenu

> **Préparation, conception et programmation : Dr. Okba Ben Atia**

---

> ⚠️ **Les résultats présentés dans cette démonstration sont issus d'un jeu de données
> synthétique. Ils servent à valider le fonctionnement du MVP et ne constituent pas des résultats
> empiriques.**

---

## Table des matières

1. [Résumé](#1-résumé)
2. [Introduction](#2-introduction)
3. [Problématique](#3-problématique)
4. [Objectifs](#4-objectifs)
5. [Questions de recherche](#5-questions-de-recherche)
6. [Sources étudiées](#6-sources-étudiées)
7. [Collecte des données](#7-collecte-des-données)
8. [Prétraitement](#8-prétraitement)
9. [Construction du réseau](#9-construction-du-réseau)
10. [Détection des communautés](#10-détection-des-communautés)
11. [Mesure de polarisation](#11-mesure-de-polarisation)
12. [Analyse lexicale](#12-analyse-lexicale)
13. [Analyse de sentiment](#13-analyse-de-sentiment)
14. [Colère et soutien](#14-colère-et-soutien)
15. [Discours haineux](#15-discours-haineux)
16. [Propagation](#16-propagation)
17. [Résultats](#17-résultats)
18. [Discussion](#18-discussion)
19. [Limites](#19-limites)
20. [Conclusion](#20-conclusion)

---

## 1. Résumé

Ce rapport présente un MVP académique destiné à l'étude de la polarisation, des communautés et de
la propagation du discours de haine sur les réseaux sociaux, autour de sujets sensibles :
arabisation, religion, immigration, identité et questions sociales et politiques connexes.

Le dispositif comprend une chaîne de traitement Python exécutée hors ligne — collecte publique,
validation, pseudonymisation, prétraitement multilingue, construction d'un réseau orienté
pondéré, détection de communautés, mesure de polarisation, analyse lexicale, classification du
sentiment, de la colère et du soutien, estimation de la toxicité et du discours potentiellement
haineux, reconstruction des cascades de propagation — et un tableau de bord Next.js en français
qui restitue les résultats produits, sans recalcul et sans modèle chargé côté navigateur.

Sept publications réelles constituent les cas d'étude initiaux : cinq sur Facebook, une sur X,
une sur Instagram. **La tentative de collecte publique n'a permis de récupérer aucune interaction
réelle**, pour des raisons documentées en section 7. Le pipeline a donc été validé sur un jeu de
données synthétique de 521 interactions entre 84 utilisateurs, réparties sur 14 publications.

Sur ce corpus de démonstration, le dispositif détecte quatre communautés (modularité 0,4337 ;
lecture indicative : polarisation modérée), met en évidence des champs lexicaux nettement
distincts, une communauté concentrant à la fois le sentiment négatif le plus élevé (44,9 %), la
colère la plus fréquente (30,9 %) et la proportion la plus forte de contenus classés
potentiellement haineux (8,8 % contre 0,8 % ailleurs), et quatorze cascades de discussion qui
franchissent toutes les frontières communautaires.

Ces résultats démontrent que le pipeline calcule ce qu'il annonce. **Ils ne constituent pas des
résultats empiriques.**

---

## 2. Introduction

Les réseaux sociaux constituent un espace majeur de discussion sur des questions socialement
sensibles. Ces discussions présentent deux propriétés régulièrement observées dans la
littérature : une tendance des échanges à se concentrer à l'intérieur de groupes d'affinité, et
la circulation de contenus hostiles susceptibles de viser collectivement des groupes de
personnes.

Étudier ces phénomènes suppose d'articuler deux niveaux d'analyse trop souvent traités
séparément : la **structure** des interactions — qui parle à qui, avec quelle fréquence — et le
**contenu** échangé — quel vocabulaire, quelle tonalité, quelle hostilité.

Ce MVP articule ces deux niveaux dans un dispositif volontairement léger, reproductible et
auditable. Il ne vise ni l'exhaustivité, ni le traitement à grande échelle, mais la
démonstration d'une chaîne complète, honnête sur ce qu'elle mesure et sur ce qu'elle ignore.

---

## 3. Problématique

Trois difficultés structurent ce travail.

**Première difficulté : l'accès aux données.** Les interactions entre utilisateurs — commentaires,
réponses, mentions, partages — constituent la matière première de toute analyse de réseau. Or les
grandes plateformes ne les exposent plus publiquement. Y accéder suppose des API soumises à
souscription ou à revue, ou des méthodes de contournement que ce projet exclut. Un dispositif
d'étude honnête doit donc être conçu **avec cette contrainte**, non contre elle.

**Deuxième difficulté : la confusion des dimensions.** Polarisation, sentiment négatif, colère,
toxicité et discours haineux sont fréquemment amalgamés. Un débat vif entre communautés
distinctes n'est pas du discours haineux ; un contenu haineux peut être formulé calmement. Cette
confusion produit des conclusions non seulement fausses, mais potentiellement dommageables pour
les personnes concernées.

**Troisième difficulté : la tentation de l'étiquetage.** Nommer automatiquement une communauté
« pro-X » ou « anti-Y » revient à substituer une inférence non validée à une interprétation
humaine. Sur des sujets touchant à la religion, à l'origine ou à l'appartenance nationale, cette
substitution est particulièrement problématique.

---

## 4. Objectifs

1. **Constituer un dispositif de collecte honnête** : tenter la récupération publique dans un
   cadre éthique strict, documenter précisément ce qui est ou non accessible, et fournir une voie
   d'import manuel analysée à l'identique.
2. **Reconstituer un réseau d'interactions** entre utilisateurs pseudonymisés et en mesurer les
   propriétés structurelles.
3. **Détecter des communautés** et mesurer leur degré de séparation, sans leur attribuer
   d'étiquette idéologique.
4. **Caractériser les contenus** : vocabulaire, sentiment, colère et soutien, toxicité et
   discours potentiellement haineux, en maintenant ces dimensions distinctes.
5. **Décrire la propagation** des contenus à travers le réseau et entre communautés.
6. **Restituer l'ensemble** dans un tableau de bord professionnel en français, sans qu'aucune
   statistique ne soit écrite en dur dans l'interface.
7. **Rester léger** : exécutable sur un ordinateur standard, déployable sur un hébergement
   gratuit, sans base de données ni backend permanent.

---

## 5. Questions de recherche

* **RQ1.** Les interactions observées forment-elles des communautés distinctes ?
* **RQ2.** Quel niveau de polarisation structurelle peut être observé ?
* **RQ3.** Les communautés utilisent-elles des champs lexicaux différents ?
* **RQ4.** Certaines communautés présentent-elles davantage de sentiment négatif ?
* **RQ5.** Certaines communautés expriment-elles davantage de colère ou de soutien ?
* **RQ6.** Certaines communautés présentent-elles davantage de contenus classifiés comme
  toxiques ou potentiellement haineux ?
* **RQ7.** Comment les contenus se propagent-ils à travers le réseau et entre communautés ?
* **RQ8.** Observe-t-on des différences entre Facebook, X et Instagram lorsque les données
  disponibles permettent une comparaison valide ?

---

## 6. Sources étudiées

Sept publications réelles constituent les cas d'étude initiaux, déclarées dans
`data/sources.json`.

| Identifiant | Plateforme | Type | URL |
|-------------|-----------|------|-----|
| `facebook_001` | Facebook | vidéo | https://www.facebook.com/share/v/18hGjKiFVK/ |
| `facebook_002` | Facebook | publication | https://www.facebook.com/share/p/1HYJ6PKM2Q/ |
| `facebook_003` | Facebook | vidéo | https://www.facebook.com/share/v/1GCZzavgcV/ |
| `facebook_004` | Facebook | publication | https://www.facebook.com/share/p/1F5HSSqfkM/ |
| `facebook_005` | Facebook | publication | https://www.facebook.com/share/p/18GdU39RoV/ |
| `x_001` | X | publication | https://x.com/i/status/2087872720012796385 |
| `instagram_001` | Instagram | reel | https://www.instagram.com/reel/DbtVlHYABVK/ |

Le champ « thématique déclarée » de chaque source est laissé à qualifier manuellement : le
dispositif n'infère pas automatiquement le sujet d'une publication.

---

## 7. Collecte des données

### 7.1 Cadre

La tentative de collecte (`analysis/collect.py`) est limitée aux métadonnées publiques exposées
sans authentification. Elle respecte sans exception : le fichier `robots.txt` de chaque
plateforme, l'absence totale d'authentification et de cookie personnel, l'absence de tout
contournement de CAPTCHA, de protection anti-bot ou de limitation d'API, une seule requête par
URL avec délai, et l'absence de recherche ou de conservation de données privées.

### 7.2 Résultat

**Aucune interaction n'a pu être récupérée automatiquement sur les sept sources.**

Deux causes se cumulent.

**Cause immédiate.** Pour les sept URLs, la lecture préalable de `robots.txt` a échoué :
`Tunnel connection failed: 403 Forbidden`. L'environnement d'exécution refuse l'accès sortant
vers `facebook.com`, `x.com` et `instagram.com`. Conformément au cadre retenu, cette restriction
n'a pas été contournée : aucune requête de contenu n'a été émise. Le dispositif est délibérément
conservateur — lorsque le protocole d'exclusion ne peut pas être vérifié, la collecte n'est pas
tentée.

**Cause structurelle.** Même avec un accès réseau complet, la collecte des interactions resterait
impossible dans ce cadre. Les publications Facebook partagées via `/share/…` exigent une session
authentifiée pour afficher les commentaires. L'accès programmatique aux publications, réponses,
reposts et citations sur X passe exclusivement par une API soumise à souscription. Les pages
Instagram `/reel/…` n'exposent au mieux que quelques métadonnées Open Graph.

En résumé : les métadonnées d'une publication peuvent parfois être lues publiquement, mais **les
interactions entre utilisateurs — matière première de cette étude — ne le sont sur aucune des
trois plateformes**.

### 7.3 Conséquence

Les sept sources sont donc en statut « Import manuel requis » du point de vue de la collecte
automatique. La voie d'acquisition retenue est l'**import manuel** au format normalisé, décrite
en section 5 de [`docs/COLLECTE_DES_DONNEES.md`](COLLECTE_DES_DONNEES.md). Cette bascule a été
vérifiée : un extrait de 47 interactions déposé dans `data/imported/` fait passer le corpus en
mode « données réelles », met à jour le statut de la seule source concernée, et supprime la
publication d'extraits de contenu.

En l'absence de données réelles, le pipeline a été validé sur le jeu synthétique
`data/sample_interactions.csv` : 521 interactions, 84 utilisateurs, 14 publications réparties sur
les sept sources déclarées.

---

## 8. Prétraitement

Le texte brut est conservé (`raw_text`) et une version nettoyée est produite (`clean_text`).

Le traitement prend en charge le français, l'arabe et les textes mixtes : normalisation Unicode,
suppression des URLs et des mentions (extraites séparément), suppression des diacritiques arabes
et du tatweel, harmonisation des formes de l'alef, du ya, du waw hamzé et du ta marbuta,
réduction des répétitions de caractères, passage en minuscules.

Les hashtags sont conservés lorsqu'ils portent une valeur analytique : le croisillon est retiré
mais le terme demeure dans le corpus. Les élisions françaises sont découpées (« l'école » →
« l » + « école »), ce qui isole le terme porteur de sens tout en préservant la négation
(« n'est pas »). Deux flux de jetons sont produits : les jetons complets, utilisés par les
classifieurs qui ont besoin des marques de négation et d'intensité, et les jetons lexicaux, mots
vides retirés, utilisés pour l'analyse lexicale.

Sur le corpus de démonstration, **511 des 521 interactions comportent un contenu textuel
exploitable** ; les 10 restantes sont des partages sans commentaire, correctement exclues des
analyses de contenu sans être exclues du réseau.

**Anonymisation.** Tous les identifiants sont pseudonymisés avant toute analyse
(`HMAC-SHA256` salé), puis remplacés à l'affichage par des étiquettes neutres
(« Utilisateur 001 »…). La table de correspondance reste locale et n'est jamais publiée. Aucun
attribut sensible n'est inféré.

---

## 9. Construction du réseau

Le réseau est un graphe **orienté et pondéré** : un nœud par utilisateur pseudonymisé, un lien de
l'auteur d'une interaction vers l'utilisateur visé, un poids égal au nombre d'interactions
agrégées entre deux comptes. Les types produisant un lien sont `comment`, `reply`, `mention`,
`share`, `repost` et `quote` ; les publications ne créent pas de lien mais alimentent le compte
de messages de leur auteur.

Sur le corpus de démonstration :

| Mesure | Valeur |
|--------|--------|
| Nœuds | 84 |
| Liens | 447 |
| Interactions agrégées | 507 |
| Densité | 0,06411 |
| Degré moyen | 10,64 |
| Réciprocité | 0,143 |
| Composantes faiblement connexes | 1 |
| Composante principale | 84 nœuds (100 %) |

Le réseau est entièrement connexe. La réciprocité de 0,143 indique que la grande majorité des
échanges sont unidirectionnels : environ une paire sur sept seulement donne lieu à un échange
dans les deux sens.

---

## 10. Détection des communautés

L'algorithme de **Louvain** est appliqué à la projection non orientée et pondérée du réseau,
avec une graine fixe garantissant la reproductibilité. Les communautés sont renumérotées par
taille décroissante et ne reçoivent que des **noms neutres**.

**Quatre communautés** sont détectées, sans utilisateur laissé de côté :

| Communauté | Utilisateurs | Messages | Interactions internes | Interactions externes |
|------------|--------------|----------|----------------------|----------------------|
| Communauté 1 | 26 | 128 | 79 | 75 |
| Communauté 2 | 22 | 123 | 88 | 73 |
| Communauté 3 | 20 | 133 | 90 | 83 |
| Communauté 4 | 16 | 137 | 90 | 89 |

Aucune étiquette idéologique n'est produite. Ce choix est méthodologique, non cosmétique : une
communauté est un agrégat d'interactions fréquentes, non un groupe d'opinion. Deux utilisateurs
en désaccord permanent sont structurellement proches dans le graphe. **L'interprétation
idéologique demeure une tâche humaine.**

---

## 11. Mesure de polarisation

La polarisation structurelle est décrite par des indicateurs simples et vérifiables, dont les
valeurs numériques sont toujours affichées :

| Indicateur | Valeur |
|------------|--------|
| Modularité | **0,4337** |
| Interactions intra-communautés | 347 |
| Interactions inter-communautés | 160 |
| Part de liens internes | **68,4 %** |
| Ratio intra / inter | **2,17** |
| Lecture indicative | **Polarisation modérée** |

Plus des deux tiers des interactions restent internes aux communautés, mais près d'un tiers les
traverse : la séparation est réelle sans être étanche.

> Les seuils employés (faible si *Q* < 0,30 ; modérée si 0,30 ≤ *Q* < 0,50 ; forte si *Q* ≥ 0,50)
> relèvent d'un usage conventionnel en analyse de réseaux. **Ils sont indicatifs et ne
> constituent pas une métrique validée de la polarisation.** Aucun « score scientifique » n'est
> fabriqué.

---

## 12. Analyse lexicale

Pour chaque combinaison communauté × plateforme sont extraits les mots fréquents (après
suppression des mots vides français et arabes), les bigrammes, les termes caractéristiques au
sens TF-IDF et les hashtags principaux.

| Communauté | Termes caractéristiques (TF-IDF) | Hashtags principaux |
|------------|----------------------------------|---------------------|
| Communauté 1 | école, arabisation, langue, universitaire, réforme, place | `#école`, `#تعريب`, `#arabisation` |
| Communauté 2 | travail, accord, logement, conditions, politique, migratoire | `#travail`, `#هجرة`, `#immigration` |
| Communauté 3 | rapport, liberté, croyance, société, valeurs, foi | `#دين`, `#tradition`, `#religion` |
| Communauté 4 | patrimoine, culturelle, années, identité, coupe, pleine | `#patrimoine`, `#identité`, `#هوية` |

**Aucun terme caractéristique n'est partagé par les quatre communautés.** Les hashtags arabes
sont correctement extraits et normalisés, ce qui valide le prétraitement multilingue.

---

## 13. Analyse de sentiment

Trois catégories — Positif, Neutre, Négatif — produites hors ligne par un dispositif lexical à
base de règles couvrant le français et l'arabe, avec gestion de la négation sur une fenêtre de
trois jetons et de l'intensification. Aucun modèle d'apprentissage automatique n'est chargé par
le tableau de bord.

Aucun modèle multilingue pré-entraîné n'a été retenu, faute de pouvoir en documenter honnêtement
les performances sur un corpus mêlant français, arabe et darija. L'analyse est donc présentée
comme **indicative**, et l'architecture demeure **remplaçable** : la fonction `classer_texte()`
constitue le point d'extension unique.

Sur 511 messages textuels : **Positif 131 (25,6 %)**, **Neutre 186 (36,4 %)**, **Négatif 194
(38,0 %)**.

| Communauté | Positif | Négatif |
|------------|---------|---------|
| Communauté 1 | 31,7 % | 35,0 % |
| Communauté 2 | 22,0 % | 40,7 % |
| Communauté 3 | 30,2 % | **31,0 %** |
| Communauté 4 | 19,1 % | **44,9 %** |

> **Aucune mesure de précision, de rappel ou de F1 n'est annoncée : aucune évaluation sur corpus
> annoté n'a été réalisée.**

---

## 14. Colère et soutien

Une classification indépendante de la précédente distingue **Colère**, **Soutien / approbation**
et **Autre / neutre**, en combinant des dictionnaires lexicaux et des marqueurs typographiques
faibles, pondérés faiblement.

Sur 511 messages : **Colère 107 (20,9 %)**, **Soutien 136 (26,6 %)**, **Autre 268 (52,5 %)**.

| Communauté | Colère | Soutien / approbation |
|------------|--------|----------------------|
| Communauté 1 | 18,7 % | 32,5 % |
| Communauté 2 | 17,1 % | 27,6 % |
| Communauté 3 | **16,3 %** | 28,7 % |
| Communauté 4 | **30,9 %** | **18,4 %** |

La Communauté 4 est la seule où la colère domine le soutien.

> Ces catégories décrivent le **contenu d'un message**. Elles ne décrivent jamais l'état
> psychologique d'une personne.

---

## 15. Discours haineux

Trois catégories mutuellement exclusives sont distinguées. La catégorie « Potentiellement
haineux » exige une **co-occurrence** entre une désignation collective et une formulation
d'exclusion, de rejet collectif ou de déshumanisation. Cette règle est volontairement
conservatrice : la seule mention d'un groupe ne déclenche aucune classification, et une critique
négative sans formulation d'exclusion reste classée « Non haineux ».

Sur 511 messages : **Non haineux 453 (88,7 %)**, **Toxique / offensant 38 (7,4 %)**,
**Potentiellement haineux 20 (3,9 %)**. Confiance moyenne sur les contenus classés : 0,613
(valeur indicative, non calibrée).

| Communauté | Toxique / offensant | Potentiellement haineux |
|------------|--------------------|------------------------|
| Communauté 1 | 8,1 % | 0,8 % |
| Communauté 2 | 7,3 % | 4,9 % |
| Communauté 3 | 6,2 % | **0,8 %** |
| Communauté 4 | 8,1 % | **8,8 %** |

Ce résultat est méthodologiquement instructif : la **toxicité** est répartie de façon homogène
(6,2 % à 8,1 %), alors que le **contenu potentiellement haineux** varie d'un facteur supérieur à
dix. Une communauté peut présenter un niveau d'invective interpersonnelle comparable aux autres
tout en produisant beaucoup plus de contenus visant collectivement un groupe. **Les deux
dimensions ne se confondent pas.**

> Il s'agit de **contenus classifiés comme potentiellement haineux**, jamais d'utilisateurs
> qualifiés de haineux. Cette classification signale un signal lexical à vérifier manuellement ;
> elle ne constitue pas une qualification juridique. Aucune performance n'est annoncée.

---

## 16. Propagation

Les cascades sont reconstruites à partir du champ `parent_id` : publication → commentaire →
réponse → partage, repost ou citation. Aucun modèle de diffusion n'est estimé ; l'analyse est
descriptive.

| Indicateur | Valeur |
|------------|--------|
| Cascades reconstruites | 14 |
| Taille moyenne | 37,2 interactions |
| Taille maximale | 65 interactions |
| Profondeur moyenne | 4,0 |
| Durée moyenne | ≈ 34 heures |
| Cascades atteignant plusieurs communautés | **14 sur 14** |

| Cascade | Source | Taille | Participants | Communautés | Négatif | Colère | Potentiellement haineux |
|---------|--------|--------|--------------|-------------|---------|--------|------------------------|
| `p006` | `facebook_003` | 65 | 40 | 4 | 45,3 % | 35,9 % | 9,4 % |
| `p003` | `facebook_002` | 55 | 38 | 4 | 40,7 % | 20,4 % | 3,7 % |
| `p005` | `facebook_003` | 55 | 40 | 4 | 48,2 % | 24,1 % | 3,7 % |

**Toutes les cascades traversent au moins deux communautés**, et les plus volumineuses en
atteignent les quatre.

---

## 17. Résultats

Synthèse par question de recherche. Le détail figure dans [`docs/RESULTATS.md`](RESULTATS.md).

| Question | Réponse sur le corpus de démonstration |
|----------|----------------------------------------|
| **RQ1** | **Oui.** Quatre communautés de 16 à 26 utilisateurs, modularité 0,4337, réseau entièrement connexe. |
| **RQ2** | **Modérée.** 68,4 % de liens internes, ratio intra/inter de 2,17. |
| **RQ3** | **Oui, nettement.** Aucun terme caractéristique commun aux quatre communautés. |
| **RQ4** | **Oui.** 44,9 % de sentiment négatif dans la Communauté 4 contre 31,0 % dans la Communauté 3. |
| **RQ5** | **Oui.** La Communauté 4 est la seule où la colère (30,9 %) dépasse le soutien (18,4 %). |
| **RQ6** | **Oui, pour le discours haineux uniquement.** Toxicité homogène (6,2–8,1 %) ; contenu potentiellement haineux de 0,8 % à 8,8 %. |
| **RQ7** | 14 cascades, profondeur 4, ≈ 34 h de durée moyenne ; **toutes** traversent plusieurs communautés. |
| **RQ8** | **Non concluant.** Corpus synthétique et volumes déséquilibrés (76,2 % Facebook). |

---

## 18. Discussion

### 18.1 Ce que le dispositif démontre

La chaîne complète fonctionne de bout en bout : un corpus au format normalisé est validé,
pseudonymisé, prétraité en français et en arabe, transformé en réseau orienté pondéré, partitionné
en communautés, caractérisé lexicalement, classé selon trois dimensions distinctes, et décomposé
en cascades — le tout par une commande unique, en quelques secondes, sur un ordinateur standard.

### 18.2 Une convergence, et son interprétation prudente

Sur le corpus de démonstration, la Communauté 4 concentre simultanément la proportion la plus
élevée de sentiment négatif, la fréquence de colère la plus forte, et une part de contenus
classés potentiellement haineux plus de dix fois supérieure à celle des Communautés 1 et 3.

Cette convergence est exactement le type de résultat que le dispositif est conçu pour **rendre
visible sans le sur-interpréter**. Elle ne dit pas que cette communauté serait « haineuse » :
elle dit que les contenus qui y ont été observés présentent, plus souvent qu'ailleurs, des
signaux lexicaux d'exclusion collective. Sur un corpus réel, un tel résultat constituerait un
point de départ pour une **lecture qualitative humaine**, non une conclusion.

### 18.3 La dissociation toxicité / discours haineux

Le résultat le plus instructif du point de vue méthodologique est que la toxicité est répartie de
façon homogène entre les communautés alors que le discours potentiellement haineux ne l'est pas.
L'invective interpersonnelle et l'hostilité visant collectivement un groupe sont deux phénomènes
distincts. Un dispositif qui les agrégerait en un « score de haine » unique masquerait
précisément la distinction qui compte.

### 18.4 Polarisation structurelle et perméabilité

Deux observations coexistent : 68,4 % des interactions restent internes aux communautés, mais
**la totalité des cascades traverse plusieurs communautés**. Autrement dit, le régime dominant
est l'échange intra-communautaire, tandis que les discussions les plus volumineuses sont
précisément celles qui franchissent les frontières.

Sur un corpus réel, cette observation appellerait un examen approfondi : les interactions
inter-communautaires relèvent-elles de la confrontation ou du dialogue ? Le dispositif actuel ne
permet pas de trancher — le graphe mesure une fréquence d'échange, pas une affinité.

### 18.5 Le choix de l'honnêteté sur les performances

Il aurait été possible d'utiliser un modèle multilingue pré-entraîné et d'en citer les
performances publiées. Ce choix a été écarté : ces performances sont mesurées sur des corpus
d'évaluation sans rapport avec un corpus mêlant français, arabe standard et darija, et les
reprendre reviendrait à annoncer une fiabilité invérifiable ici.

Le dispositif retenu est plus modeste et **explicitement présenté comme indicatif**, avec une
architecture remplaçable en un point unique. La prochaine étape naturelle du projet est la
constitution d'un corpus annoté permettant une évaluation réelle.

### 18.6 La contrainte d'accès comme donnée du problème

L'impossibilité de collecter automatiquement les interactions n'est pas un échec du dispositif :
c'est une caractéristique de l'écosystème actuel, documentée avec précision. Le MVP y répond par
une architecture indifférente à l'origine des données : collecte publique, export de plateforme,
CSV manuel ou JSON produisent exactement les mêmes analyses.

---

## 19. Limites

Les limites sont détaillées dans [`docs/LIMITES.md`](LIMITES.md). Les principales :

1. **Aucune donnée réelle n'a été collectée.** Les résultats proviennent d'un jeu synthétique et
   ne sont pas empiriques.
2. **Aucune performance de classification ne peut être annoncée** : aucune évaluation sur corpus
   annoté n'a été réalisée, pour aucun des trois dispositifs.
3. **L'approche lexicale ignore l'ironie, le sarcasme, l'implicite et les formulations codées.**
   Une dénonciation d'un propos haineux peut être classée à tort dans une catégorie négative.
4. **La darija en caractères latins n'est couverte que partiellement**, ce qui introduit un biais
   linguistique non réparti aléatoirement.
5. **Le graphe reflète les seules données disponibles** : la densité observée est une borne
   inférieure de la densité réelle.
6. **Toutes les interactions ont le même sens dans le graphe** : une réponse hostile et une
   réponse approbatrice produisent le même lien.
7. **La partition de Louvain n'est pas unique** ; les seuils de polarisation sont conventionnels.
8. **L'analyse de propagation dépend entièrement du champ `parent_id`.**
9. **Aucune inférence causale n'est possible**, et les résultats ne se généralisent ni à une
   plateforme ni à une population.
10. **La comparaison entre plateformes n'est pas valide** dans le corpus actuel.

---

## 20. Conclusion

Ce MVP démontre qu'il est possible de construire un dispositif d'étude de la polarisation et du
discours de haine qui soit à la fois **complet dans sa chaîne de traitement** — de l'acquisition
des données à la restitution visuelle — et **strict dans ses affirmations**.

Trois principes ont structuré sa conception. Premièrement, ne jamais présenter comme analysé ce
qui n'a pas été réellement récupéré : les sept sources déclarées portent le statut effectivement
constaté. Deuxièmement, ne jamais confondre les dimensions mesurées : polarisation, sentiment
négatif, colère, toxicité et discours haineux restent séparés à chaque étape, et le corpus de
démonstration montre concrètement pourquoi cette séparation importe. Troisièmement, ne jamais
substituer une inférence automatique à une interprétation humaine : les communautés ne reçoivent
que des noms neutres, et les classifications de contenu sont présentées comme indicatives.

Sur le plan technique, l'architecture retenue — pipeline Python hors ligne, résultats JSON
statiques, tableau de bord Next.js — tient l'objectif de légèreté : aucune base de données, aucun
backend permanent, aucun modèle exécuté en production, un déploiement sur hébergement gratuit et
une exécution complète en quelques secondes sur un ordinateur standard.

Deux prolongements se dégagent. Le premier est l'**acquisition de données réelles**, par export
de plateforme ou par accès API autorisé, qui permettrait de produire les résultats empiriques
que ce rapport ne prétend pas fournir. Le second est la **constitution d'un corpus annoté** en
français, en arabe et en darija, qui permettrait d'évaluer réellement les classifieurs et de
remplacer les heuristiques actuelles par des modèles dont les performances seraient, elles,
mesurables et publiables.

En l'état, le dispositif est fonctionnel, reproductible, documenté et démontrable. Ce qu'il
mesure, il le mesure de façon transparente ; ce qu'il ne mesure pas, il le dit.

---

> **Rappel final : les résultats présentés dans cette démonstration sont issus d'un jeu de
> données synthétique. Ils servent à valider le fonctionnement du MVP et ne constituent pas des
> résultats empiriques.**

---

*Préparation, conception et programmation : Dr. Okba Ben Atia*
