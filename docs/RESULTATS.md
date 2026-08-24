# Résultats

> Préparation, conception et programmation : **Dr. Okba Ben Atia**

> ⚠️ **Les résultats présentés dans ce document sont issus d'un jeu de données synthétique. Ils
> servent à valider le fonctionnement du MVP et ne constituent pas des résultats empiriques.**

Corpus analysé : `data/sample_interactions.csv` — 521 interactions, 84 utilisateurs,
14 publications, réparties sur les sept sources déclarées.
Exécution du 24 août 2026. Tous les chiffres ci-dessous proviennent de `public/data/*.json`.

Pour régénérer ces résultats :

```bash
python analysis/run_analysis.py
```

---

## 1. Volume et qualité des données

| Indicateur | Valeur |
|------------|--------|
| Sources déclarées | 7 |
| Sources avec données réelles importées | **0** |
| Sources nécessitant un import manuel | **7** |
| Sources couvertes par le corpus synthétique | 7 (statut « Données de démonstration ») |
| Publications | 14 |
| Interactions | 521 |
| Utilisateurs pseudonymisés | 84 |
| Messages comportant du texte | 511 |
| Lignes ignorées | 0 |
| Doublons supprimés | 0 |
| Horodatages invalides | 0 |
| Types d'interaction non reconnus | aucun |
| Messages sans texte | 10 |

### Répartition par plateforme

| Plateforme | Interactions | Part | Publications |
|-----------|--------------|------|--------------|
| Facebook  | 397 | 76,2 % | 10 |
| X         | 74  | 14,2 % | 2  |
| Instagram | 50  | 9,6 %  | 2  |

Ce déséquilibre reflète la composition des sources déclarées (cinq publications Facebook contre
une sur X et une sur Instagram). Il doit être gardé à l'esprit pour toute comparaison entre
plateformes (RQ8).

---

## 2. Réseau (RQ1)

| Mesure | Valeur |
|--------|--------|
| Nœuds | 84 |
| Liens | 447 |
| Interactions agrégées | 507 |
| Densité | 0,06411 |
| Degré moyen | 10,64 |
| Degré entrant moyen | 5,32 |
| Degré sortant moyen | 5,32 |
| Réciprocité | 0,143 |
| Composantes faiblement connexes | 1 |
| Composante principale | 84 nœuds (100 %) |
| Intermédiarité | calcul exact |

Le réseau est **entièrement connexe** : aucun utilisateur isolé. Sur 521 interactions,
507 produisent un lien orienté ; les 14 restantes sont les publications d'origine, qui ne créent
pas de lien.

La réciprocité de 0,143 indique que la grande majorité des échanges sont **unidirectionnels** :
seule une paire sur sept environ donne lieu à un échange dans les deux sens.

### Utilisateurs les plus centraux

| Utilisateur | Communauté | Degré | Centralité de degré | Intermédiarité |
|-------------|------------|-------|---------------------|----------------|
| Utilisateur 023 | Communauté 3 | 27 | 0,325 | 0,060 |
| Utilisateur 054 | Communauté 3 | 27 | 0,325 | 0,088 |
| Utilisateur 021 | Communauté 2 | 26 | 0,313 | 0,083 |
| Utilisateur 004 | Communauté 1 | 24 | 0,289 | 0,093 |
| Utilisateur 008 | Communauté 4 | 22 | 0,265 | 0,048 |

---

## 3. Communautés (RQ1)

**Quatre communautés** ont été détectées par Louvain (`python-louvain`), avec une modularité de
**0,4337**.

| Communauté | Utilisateurs | Messages | Interactions internes | Interactions externes | Part interne |
|------------|--------------|----------|----------------------|----------------------|--------------|
| Communauté 1 | 26 | 128 | 79 | 75 | 51,3 % |
| Communauté 2 | 22 | 123 | 88 | 73 | 54,7 % |
| Communauté 3 | 20 | 133 | 90 | 83 | 52,0 % |
| Communauté 4 | 16 | 137 | 90 | 89 | 50,3 % |

Aucun utilisateur n'est laissé hors communauté. Les tailles sont comparables (16 à 26
utilisateurs), sans communauté dominante.

> Les parts internes ci-dessus sont calculées **par communauté**, chaque interaction externe
> étant comptée pour les deux communautés qu'elle relie. Elles ne se somment donc pas à la part
> globale de liens internes reportée en section 4.

---

## 4. Polarisation structurelle (RQ2)

| Indicateur | Valeur |
|------------|--------|
| Modularité | **0,4337** |
| Interactions intra-communautés | 347 |
| Interactions inter-communautés | 160 |
| Interactions totales | 507 |
| Part de liens internes | **68,4 %** |
| Ratio intra / inter | **2,17** |
| Lecture indicative | **Polarisation modérée** |

Plus des deux tiers des interactions restent à l'intérieur des communautés, mais près d'un tiers
les traverse : la séparation est réelle sans être étanche.

> **Seuils indicatifs** : faible si *Q* < 0,30 ; modérée si 0,30 ≤ *Q* < 0,50 ; forte si
> *Q* ≥ 0,50. Ces seuils relèvent d'un usage conventionnel en analyse de réseaux et **ne
> constituent pas une métrique validée de la polarisation**.

---

## 5. Champs lexicaux (RQ3)

Les quatre communautés présentent des **champs lexicaux nettement distincts**.

| Communauté | Termes caractéristiques (TF-IDF) | Hashtags principaux |
|------------|----------------------------------|---------------------|
| Communauté 1 | école, arabisation, langue, universitaire, réforme, place | `#école`, `#تعريب`, `#arabisation`, `#université`, `#langue` |
| Communauté 2 | travail, accord, logement, conditions, politique, migratoire | `#travail`, `#هجرة`, `#frontières`, `#immigration`, `#économie` |
| Communauté 3 | rapport, liberté, croyance, société, valeurs, foi | `#دين`, `#tradition`, `#société`, `#valeurs`, `#religion` |
| Communauté 4 | patrimoine, culturelle, années, identité, coupe, pleine | `#patrimoine`, `#culture`, `#identité`, `#هوية`, `#nation` |

Aucun terme caractéristique n'est partagé entre les quatre communautés : les vocabulaires se
recouvrent peu, alors même qu'un tiers des interactions traverse les frontières communautaires.

Termes les plus fréquents sur l'ensemble du corpus : *rapport, école, travail, accord, années,
publié, dernier, abordait, page, exactement, place, bravo*. Le corpus comporte des messages en
français, en arabe et mixtes ; les hashtags arabes (`#تعريب`, `#هجرة`, `#دين`, `#هوية`) sont
correctement extraits et normalisés.

---

## 6. Sentiment (RQ4)

Sur 511 messages textuels :

| Catégorie | Nombre | Part |
|-----------|--------|------|
| Positif | 131 | 25,6 % |
| Neutre  | 186 | 36,4 % |
| Négatif | 194 | 38,0 % |

### Par communauté

| Communauté | Messages | Positif | Négatif |
|------------|----------|---------|---------|
| Communauté 1 | 123 | 31,7 % | 35,0 % |
| Communauté 2 | 123 | 22,0 % | 40,7 % |
| Communauté 3 | 129 | 30,2 % | **31,0 %** |
| Communauté 4 | 136 | 19,1 % | **44,9 %** |

La Communauté 4 présente la proportion de sentiment négatif la plus élevée (44,9 %) et la plus
faible proportion de sentiment positif (19,1 %). L'écart avec la Communauté 3 (31,0 % de
négatif) est de près de 14 points.

### Par plateforme

| Plateforme | Messages | Positif | Négatif |
|-----------|----------|---------|---------|
| Facebook  | 389 | 25,5 % | 39,6 % |
| Instagram | 49  | 20,4 % | 38,8 % |
| X         | 73  | 30,1 % | 28,8 % |

---

## 7. Colère et soutien (RQ5)

| Catégorie | Nombre | Part |
|-----------|--------|------|
| Colère | 107 | 20,9 % |
| Soutien / approbation | 136 | 26,6 % |
| Autre / neutre | 268 | 52,5 % |

### Par communauté

| Communauté | Colère | Soutien / approbation |
|------------|--------|----------------------|
| Communauté 1 | 18,7 % | 32,5 % |
| Communauté 2 | 17,1 % | 27,6 % |
| Communauté 3 | **16,3 %** | 28,7 % |
| Communauté 4 | **30,9 %** | **18,4 %** |

La Communauté 4 est la seule où la colère domine le soutien. L'écart de colère avec la
Communauté 3 atteint 14,6 points.

### Par plateforme

| Plateforme | Colère | Soutien / approbation |
|-----------|--------|----------------------|
| Facebook  | 22,1 % | 26,5 % |
| Instagram | 22,5 % | 20,4 % |
| X         | 13,7 % | 31,5 % |

> Ces catégories décrivent le **contenu d'un message**, jamais l'état psychologique d'une
> personne.

---

## 8. Toxicité et discours potentiellement haineux (RQ6)

| Catégorie | Nombre | Part |
|-----------|--------|------|
| Non haineux | 453 | 88,7 % |
| Toxique / offensant | 38 | 7,4 % |
| Potentiellement haineux | 20 | 3,9 % |

Confiance moyenne sur les contenus classés : **0,613** (valeur indicative, non calibrée).

### Par communauté

| Communauté | Messages | Toxique / offensant | Potentiellement haineux |
|------------|----------|--------------------|------------------------|
| Communauté 1 | 123 | 8,1 % | 0,8 % |
| Communauté 2 | 123 | 7,3 % | 4,9 % |
| Communauté 3 | 129 | 6,2 % | **0,8 %** |
| Communauté 4 | 136 | 8,1 % | **8,8 %** |

La toxicité est répartie de façon relativement homogène (6,2 % à 8,1 %), alors que le contenu
classé potentiellement haineux est très inégalement distribué : 8,8 % dans la Communauté 4
contre 0,8 % dans les Communautés 1 et 3, soit un rapport supérieur à dix.

**Cet écart illustre que toxicité et discours haineux ne se confondent pas.** Une communauté peut
présenter un niveau d'invective interpersonnelle comparable à celle des autres tout en produisant
dix fois plus de contenus visant collectivement un groupe.

### Par plateforme

| Plateforme | Messages | Toxique / offensant | Potentiellement haineux |
|-----------|----------|--------------------|------------------------|
| Facebook  | 389 | 6,9 % | 4,4 % |
| Instagram | 49  | 10,2 % | 0,0 % |
| X         | 73  | 8,2 % | 4,1 % |

Les effectifs Instagram (49 messages) et X (73 messages) sont trop faibles pour qu'un écart de
quelques points soit interprétable.

### Par source

| Source | Messages | Potentiellement haineux |
|--------|----------|------------------------|
| `facebook_001` | 46  | 0,0 % |
| `facebook_002` | 99  | 4,0 % |
| `facebook_003` | 118 | 6,8 % |
| `facebook_004` | 73  | 5,5 % |
| `facebook_005` | 53  | 1,9 % |
| `instagram_001`| 49  | 0,0 % |
| `x_001`        | 73  | 4,1 % |

---

## 9. Propagation (RQ7)

| Indicateur | Valeur |
|------------|--------|
| Cascades reconstruites | 14 |
| Taille moyenne | 37,2 interactions |
| Taille maximale | 65 interactions |
| Profondeur moyenne | 4,0 |
| Profondeur maximale | 4 |
| Durée moyenne | 2 039 minutes (≈ 34 heures) |
| Cascades atteignant plusieurs communautés | **14 sur 14** |

### Principales cascades

| Cascade | Source | Taille | Profondeur | Participants | Communautés atteintes | Négatif | Colère | Potentiellement haineux |
|---------|--------|--------|-----------|--------------|----------------------|---------|--------|------------------------|
| `p006` | `facebook_003` | 65 | 4 | 40 | 4 | 45,3 % | 35,9 % | 9,4 % |
| `p003` | `facebook_002` | 55 | 4 | 38 | 4 | 40,7 % | 20,4 % | 3,7 % |
| `p005` | `facebook_003` | 55 | 4 | 40 | 4 | 48,2 % | 24,1 % | 3,7 % |

**Toutes les cascades traversent au moins deux communautés**, et les plus volumineuses en
atteignent les quatre. Autrement dit : bien que les échanges se concentrent majoritairement à
l'intérieur des communautés (68,4 % des interactions), les cascades de discussion, elles,
franchissent systématiquement les frontières communautaires.

Les proportions de contenus classés négatifs, en colère ou potentiellement haineux varient
sensiblement d'une cascade à l'autre (de 3,7 % à 9,4 % pour le contenu potentiellement haineux),
sans que ce dispositif descriptif permette d'en identifier la cause.

---

## 10. Comparaison entre plateformes (RQ8)

Une comparaison valide suppose des volumes et des modes de collecte comparables. Dans le corpus
actuel :

* Facebook représente 76,2 % des interactions, contre 14,2 % pour X et 9,6 % pour Instagram ;
* les trois plateformes proviennent du **même jeu synthétique**, produit par un générateur
  unique.

Les écarts observés — X apparaissant moins négatif (28,8 % contre 39,6 % sur Facebook) et moins
en colère (13,7 % contre 22,1 %) — **ne peuvent pas être interprétés comme une différence
réelle entre plateformes**. Ils reflètent la composition du corpus synthétique.

**Conclusion pour RQ8 : les données disponibles ne permettent pas de comparaison valide entre
Facebook, X et Instagram.** Cette question restera ouverte tant que des données réelles
comparables n'auront pas été importées.

---

## 11. Synthèse par question de recherche

| Question | Réponse sur le corpus de démonstration |
|----------|----------------------------------------|
| **RQ1** — Communautés distinctes ? | Oui : 4 communautés de 16 à 26 utilisateurs, modularité 0,4337, réseau entièrement connexe. |
| **RQ2** — Niveau de polarisation structurelle ? | Modérée : 68,4 % de liens internes, ratio intra/inter de 2,17. |
| **RQ3** — Champs lexicaux différents ? | Oui, nettement : aucun terme caractéristique commun aux quatre communautés. |
| **RQ4** — Davantage de sentiment négatif ? | Oui : 44,9 % dans la Communauté 4 contre 31,0 % dans la Communauté 3. |
| **RQ5** — Davantage de colère ou de soutien ? | Oui : la Communauté 4 est la seule où la colère (30,9 %) dépasse le soutien (18,4 %). |
| **RQ6** — Davantage de contenus toxiques ou haineux ? | Toxicité homogène (6,2–8,1 %) ; contenu potentiellement haineux très inégal (0,8 % à 8,8 %). |
| **RQ7** — Comment les contenus se propagent-ils ? | 14 cascades, profondeur 4, ≈ 34 h de durée moyenne ; **toutes** traversent plusieurs communautés. |
| **RQ8** — Différences entre plateformes ? | **Non concluant** : corpus synthétique et volumes déséquilibrés. |

---

## 12. Rappel

> Ces résultats proviennent d'un jeu de données **synthétique**. Ils démontrent que le pipeline
> calcule ce qu'il annonce et que le tableau de bord restitue fidèlement ces calculs. **Ils ne
> constituent pas des résultats empiriques** et ne permettent aucune conclusion sur les
> discussions réelles associées aux sept sources déclarées.

Pour produire des résultats empiriques, importer des données réelles au format normalisé dans
`data/imported/` et relancer `python analysis/run_analysis.py`. Le tableau de bord basculera
automatiquement en mode « données réelles ».

---

*Préparation, conception et programmation : Dr. Okba Ben Atia*
