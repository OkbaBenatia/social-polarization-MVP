# Limites

> Préparation, conception et programmation : **Dr. Okba Ben Atia**

Ce document recense les limites du MVP. Il est délibérément explicite : une limite documentée
vaut mieux qu'une performance annoncée sans preuve.

---

## 1. Limites de la collecte

### 1.1 Aucune interaction réelle récupérée automatiquement

Sur les sept sources déclarées, **aucune interaction n'a pu être récupérée automatiquement**.

Deux causes se cumulent :

* **Cause immédiate** — l'environnement d'exécution utilisé refuse l'accès sortant vers
  `facebook.com`, `x.com` et `instagram.com`. La lecture préalable de `robots.txt` a échoué avec
  `Tunnel connection failed: 403 Forbidden`. Conformément au cadre retenu, cette restriction n'a
  pas été contournée : aucune requête de contenu n'a été émise.
* **Cause structurelle** — même avec un accès réseau complet, les commentaires, réponses,
  mentions, partages, reposts et citations ne sont exposés publiquement par aucune des trois
  plateformes. Leur récupération légitime suppose une API autorisée (API Graph pour Facebook et
  Instagram, API X pour X), soumise à souscription ou à revue de la plateforme.

**Conséquence** : les résultats actuellement publiés proviennent d'un jeu de données
synthétique.

### 1.2 Fragilité des URLs de partage

Les URLs de la forme `facebook.com/share/…` ou `instagram.com/reel/…?igsh=…` sont des
redirections opaques. Elles ne garantissent ni la stabilité de l'identifiant, ni la
disponibilité future du contenu. Une publication supprimée, rendue privée ou géo-restreinte
devient inaccessible sans préavis.

### 1.3 Import manuel : biais de sélection

L'import manuel introduit un biais de sélection difficile à quantifier : les interactions
retenues dépendent de ce qui a été observé et saisi. Un échantillon ainsi constitué n'est pas
représentatif de la discussion complète autour d'une publication.

---

## 2. Limites du corpus

### 2.1 Nature synthétique des résultats actuels

Tant qu'aucun fichier n'est déposé dans `data/imported/`, le pipeline analyse
`data/sample_interactions.csv`, **entièrement fabriqué**. Les résultats correspondants valident
le fonctionnement du dispositif et **ne constituent en aucun cas des résultats empiriques**.

Cette nature est signalée dans les neuf fichiers JSON produits (bloc `jeu_de_donnees`) et sur
chaque page du tableau de bord. Données réelles et synthétiques ne sont **jamais** mélangées.

### 2.2 Le jeu de démonstration ne mesure pas la qualité des classifieurs

Le générateur produit des messages à partir de gabarits organisés par registre. Ces registres ne
sont **pas** écrits dans le fichier : ils ne constituent donc pas une vérité terrain, et les
résultats obtenus sur ce corpus ne permettent aucune évaluation des classifieurs.

### 2.3 Échelle

Le MVP est dimensionné pour quelques centaines à quelques milliers d'interactions, sur un
ordinateur standard. Au-delà, la centralité d'intermédiarité passe en mode échantillonné et
l'export réseau est borné à 1 000 nœuds. Les mesures restent calculées sur l'ensemble du graphe,
mais l'affichage est tronqué.

---

## 3. Limites du traitement du texte

### 3.1 Couverture linguistique inégale

* Le français est le mieux couvert : dictionnaires plus fournis, gestion de la négation et de
  l'élision.
* L'arabe standard est couvert par une normalisation orthographique et des dictionnaires plus
  courts.
* **La darija écrite en caractères latins n'est couverte que partiellement.** Les graphies
  variables (« hadchi », « hadshi », « had chi »), les chiffres-lettres (« 3 », « 7 », « 9 ») et
  l'alternance codique ne font l'objet d'aucun traitement spécifique.

Ce choix évite une complexité disproportionnée pour un MVP, mais introduit un **biais
linguistique** : une partie du corpus est moins bien analysée, et cette partie n'est pas répartie
aléatoirement entre les communautés.

### 3.2 Absence d'analyse morphologique

Aucune lemmatisation ni racinisation n'est appliquée. Les formes fléchies d'un même mot sont
comptées séparément, ce qui disperse les fréquences et peut sous-estimer l'importance de
certains termes.

### 3.3 Détection de langue sommaire

La langue est estimée à partir des seuls systèmes d'écriture présents. Un texte en darija
latinisée est classé « fr », un texte en anglais également.

---

## 4. Limites des classifications automatiques

### 4.1 Aucune performance ne peut être annoncée

**Aucune évaluation sur corpus annoté n'a été réalisée.** Aucune mesure de précision, de rappel
ou de F1 n'est donc annoncée, ni pour le sentiment, ni pour la colère/soutien, ni pour la
toxicité. Toute valeur de ce type serait fabriquée.

Les trois dispositifs sont explicitement déclarés `performance_evaluee: false` dans les fichiers
JSON produits.

### 4.2 Limites intrinsèques d'une approche lexicale

* **Ironie et sarcasme** — non détectés. « Bravo, encore une réussite » sera classé positif.
* **Implicite et sous-entendu** — non détectés.
* **Formulations codées** — les euphémismes et détournements lexicaux échappent à toute liste
  fermée.
* **Citation et dénonciation** — un message citant un propos haineux pour le dénoncer sera
  vraisemblablement classé dans une catégorie négative. C'est un faux positif structurel de
  l'approche.
* **Contexte** — chaque message est classé isolément, sans tenir compte de la conversation.
* **Dictionnaires courts** — volontairement restreints et donc incomplets ; leur composition
  reflète des choix qui sont eux-mêmes une limite.

### 4.3 Confiance indicative

Les valeurs de confiance publiées sont dérivées de l'intensité des signaux lexicaux détectés.
**Ce ne sont pas des probabilités calibrées.** Elles permettent de trier des résultats, non de
quantifier une incertitude.

### 4.4 Distinctions à maintenir

> polarisation ≠ sentiment négatif ≠ colère ≠ toxicité ≠ discours haineux

Ces cinq dimensions sont mesurées séparément et ne doivent jamais être additionnées, substituées
ou présentées comme équivalentes. Un débat vif entre communautés distinctes n'est pas du
discours haineux ; un contenu haineux peut être formulé calmement.

---

## 5. Limites de l'analyse de réseau

### 5.1 Le graphe reflète les données disponibles

Un lien n'existe que si l'interaction figure dans le corpus importé. Les interactions non
récupérées — commentaires supprimés, réponses manquantes, partages privés — n'apparaissent pas.
La densité observée est donc une **borne inférieure** de la densité réelle.

### 5.2 Toutes les interactions ont le même sens

Une réponse hostile et une réponse approbatrice produisent le même lien, de même poids. Le
graphe mesure une **fréquence d'échange**, pas une affinité. C'est précisément pourquoi les
communautés ne reçoivent aucune étiquette idéologique.

### 5.3 Centralité d'intermédiarité approchée

Au-delà de 800 nœuds, l'intermédiarité est estimée par échantillonnage (200 pivots). Les valeurs
sont alors approchées ; le tableau de bord signale le mode de calcul employé.

---

## 6. Limites de la détection de communautés

### 6.1 Partition non unique

Louvain est stochastique et procède par optimisation gloutonne. Une graine fixe (42) garantit la
reproductibilité, mais une autre graine ou un autre algorithme peut produire une partition
différente, de modularité comparable.

### 6.2 Perte de l'orientation

La détection s'applique à la projection non orientée : l'asymétrie des échanges — qui répond à
qui — n'est pas exploitée à cette étape, alors qu'elle est disponible dans le graphe orienté.

### 6.3 Résolution

Louvain souffre d'une limite de résolution connue : les petites communautés peuvent être
fusionnées dans des ensembles plus larges. Aucun paramètre de résolution n'est exposé dans ce
MVP.

### 6.4 Une communauté n'est pas un camp

Une communauté détectée est un **agrégat d'interactions fréquentes**. L'interpréter comme un
groupe d'opinion est une erreur : deux utilisateurs en désaccord permanent sont structurellement
proches. C'est pourquoi seule une numérotation neutre est produite, et pourquoi
**l'interprétation reste une tâche humaine**.

---

## 7. Limites de la mesure de polarisation

### 7.1 Seuils conventionnels

Les seuils 0,30 et 0,50 relèvent d'un usage courant en analyse de réseaux. **Ils ne constituent
pas une métrique validée de la polarisation.** Les valeurs numériques sont donc systématiquement
affichées à côté de la lecture qualitative, et l'avertissement accompagne les résultats.

### 7.2 Polarisation structurelle uniquement

Ce qui est mesuré est la **séparation structurelle des échanges**, non l'écart des opinions, non
l'hostilité, non la radicalisation. La polarisation d'opinion — au sens de la science politique —
exigerait des données d'attitude dont ce dispositif ne dispose pas.

### 7.3 Dépendance à la partition

La modularité dépend de la partition retenue. Une partition différente produit une modularité
différente sur le même graphe.

---

## 8. Limites de l'analyse de propagation

### 8.1 Dépendance totale au champ `parent_id`

Sans `parent_id`, toutes les interactions sont des racines : la profondeur observée est nulle et
aucune cascade n'est reconstruite. La qualité de cette analyse est donc entièrement conditionnée
par la qualité de l'import.

### 8.2 Horodatages

Les durées ne sont calculées que si au moins deux horodatages valides sont disponibles dans la
cascade. Des horodatages absents, tronqués ou exprimés dans des fuseaux hétérogènes faussent la
mesure.

### 8.3 Analyse descriptive uniquement

Aucun modèle de diffusion n'est estimé. Les indicateurs produits — taille, profondeur, durée,
communautés atteintes — décrivent ce qui est observé, sans modéliser ni prédire.

---

## 9. Limites d'interprétation

### 9.1 Aucune causalité

Le dispositif produit des **co-occurrences et des structures observées**. Il ne permet aucune
inférence causale. Qu'une communauté présente davantage de contenus classés en colère
n'établit pas que sa structure en soit la cause, ni l'inverse.

### 9.2 Pas de généralisation

Les résultats portent sur les seules interactions importées, autour des seules sources
déclarées. Ils ne se généralisent ni à une plateforme, ni à une population, ni à un débat public.

### 9.3 Comparaisons entre plateformes

La comparaison Facebook / X / Instagram (RQ8) n'est valide que si les volumes et les modes de
collecte sont comparables. Lorsqu'une plateforme est très minoritaire dans le corpus, l'écart
observé relève au moins autant de la collecte que du contenu. Le tableau de bord affiche les
effectifs à côté des proportions pour permettre ce contrôle.

### 9.4 Aucun profilage individuel

Le projet analyse des contenus et des structures collectives. Il ne caractérise aucune personne,
n'infère aucun attribut sensible, et ne qualifie aucun utilisateur de haineux.

---

## 10. Limites techniques du tableau de bord

* Les résultats sont **statiques** : ils reflètent la dernière exécution du pipeline. Aucun
  calcul n'est effectué à la volée.
* Le réseau affiché est borné à 1 000 nœuds ; au-delà, l'affichage est tronqué par degré
  décroissant.
* Les arbres de cascade détaillés sont limités aux douze plus grandes cascades et à 120 nœuds
  chacun.
* La disposition du graphe est recalculée à chaque changement de filtre ou de thème : la
  position des nœuds n'est pas stable d'un rendu à l'autre.

---

*Préparation, conception et programmation : Dr. Okba Ben Atia*
