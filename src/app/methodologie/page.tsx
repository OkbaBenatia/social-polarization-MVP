import type { Metadata } from "next";

import { BandeauJeuDeDonnees } from "@/components/BandeauJeuDeDonnees";
import { Avertissement } from "@/components/ui/Avertissement";
import { Carte } from "@/components/ui/Carte";
import { EntetePage } from "@/components/ui/EntetePage";
import {
  lireCommunautes,
  lireDiscoursHaineux,
  lireEmotions,
  lireOverview,
  lireSentiment,
} from "@/lib/data";
import { decimal } from "@/lib/format";

export const metadata: Metadata = { title: "Méthodologie" };

const SECTIONS = [
  { id: "objectif", titre: "1. Objectif" },
  { id: "sources", titre: "2. Sources" },
  { id: "collecte", titre: "3. Collecte" },
  { id: "anonymisation", titre: "4. Anonymisation" },
  { id: "preprocessing", titre: "5. Prétraitement" },
  { id: "reseau", titre: "6. Réseau" },
  { id: "communautes", titre: "7. Communautés" },
  { id: "modularite", titre: "8. Modularité" },
  { id: "polarisation", titre: "9. Polarisation" },
  { id: "lexique", titre: "10. Analyse lexicale" },
  { id: "sentiment", titre: "11. Sentiment" },
  { id: "emotions", titre: "12. Colère et soutien" },
  { id: "haine", titre: "13. Discours haineux" },
  { id: "propagation", titre: "14. Propagation" },
  { id: "limites", titre: "15. Limites" },
];

export default function PageMethodologie() {
  const overview = lireOverview();
  const communautes = lireCommunautes();
  const sentiment = lireSentiment();
  const emotions = lireEmotions();
  const haine = lireDiscoursHaineux();

  return (
    <>
      <EntetePage
        titre="Méthodologie"
        description="Description complète de la chaîne de traitement, des choix méthodologiques et des limites de l'étude."
      >
        <div className="space-y-3">
          <Carte className="border-teal-600/30 bg-teal-50/60 dark:border-teal-400/30 dark:bg-teal-400/5">
            <p className="text-sm font-medium text-ardoise-900 dark:text-white">
              Préparation, conception et programmation : Dr. Okba Ben Atia
            </p>
            <p className="mt-1 text-sm text-ardoise-600 dark:text-ardoise-400">
              Étude de la polarisation et de la propagation du discours de haine sur les réseaux
              sociaux — analyse de réseaux, détection de communautés et analyse automatique du
              contenu.
            </p>
          </Carte>
          {overview ? <BandeauJeuDeDonnees jeu={overview.jeu_de_donnees} /> : null}
        </div>
      </EntetePage>

      <nav aria-label="Sommaire" className="mb-8">
        <Carte>
          <h2 className="mb-3 text-sm font-semibold text-ardoise-800 dark:text-ardoise-100">
            Sommaire
          </h2>
          <ul className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2 lg:grid-cols-3">
            {SECTIONS.map((section) => (
              <li key={section.id}>
                <a
                  href={`#${section.id}`}
                  className="text-teal-700 underline-offset-4 hover:underline dark:text-teal-400"
                >
                  {section.titre}
                </a>
              </li>
            ))}
          </ul>
        </Carte>
      </nav>

      <div className="space-y-6">
        <Section id="objectif" titre="1. Objectif">
          <p>
            L'étude vise à décrire, sur un corpus d'interactions publiques, la structure des
            échanges autour de sujets sensibles — arabisation, religion, immigration, identité et
            questions sociales et politiques connexes. Elle poursuit trois objectifs :
            reconstituer un réseau d'interactions entre utilisateurs, y détecter des communautés
            et mesurer leur degré de séparation, puis caractériser les contenus échangés
            (vocabulaire, sentiment, colère et soutien, toxicité) et leur propagation.
          </p>
          <p>
            Il s'agit d'un MVP académique fonctionnel, et non d'une plateforme de traitement à
            grande échelle. L'ensemble des calculs est effectué hors ligne en Python ; le tableau
            de bord ne fait que restituer des résultats déjà produits.
          </p>
        </Section>

        <Section id="sources" titre="2. Sources">
          <p>
            Les sources initiales de l'étude sont sept publications réelles : cinq sur Facebook,
            une sur X et une sur Instagram. Elles sont déclarées dans{" "}
            <code>data/sources.json</code> et listées, avec leur statut de collecte, sur la page
            « Sources étudiées ».
          </p>
          <p>
            Aucune source n'est présentée comme analysée tant que ses données n'ont pas été
            réellement récupérées ou importées. Quatre statuts sont possibles : données
            disponibles, accès partiel, import manuel requis, données de démonstration.
          </p>
        </Section>

        <Section id="collecte" titre="3. Collecte">
          <p>
            Une tentative de collecte publique est réalisée par <code>analysis/collect.py</code>.
            Pour chaque source, deux voies d&apos;accès sont évaluées : la page publique de la
            publication et le point d&apos;accès oEmbed officiel de la plateforme. Les règles
            suivantes sont appliquées sans exception : respect du fichier{" "}
            <code>robots.txt</code> de chaque domaine sollicité, lu avant toute requête, aucune
            authentification ni cookie personnel, aucun contournement de CAPTCHA, de protection
            anti-bot ou de limitation d&apos;API, une seule requête par voie autorisée avec délai
            entre les sources, et aucune recherche de données privées.
          </p>
          <p>
            Résultat de l&apos;exécution du 24 août 2026, menée depuis un environnement disposant
            d&apos;un accès réseau sortant complet : les 14 voies évaluées ont toutes été
            refusées par le protocole d&apos;exclusion des plateformes. Aucune interaction
            n&apos;a été récupérée automatiquement ; les sept sources nécessitent un import
            manuel. Le détail voie par voie est consultable sur la page « Sources étudiées ».
          </p>
          <p>
            Lorsque les plateformes ne permettent pas la récupération automatisée — ce qui est
            le cas général pour les commentaires, réponses, mentions et partages — le projet
            bascule sur un import manuel au format normalisé (
            <code>data/import_template.csv</code>). Le pipeline analyse rigoureusement les mêmes
            données, quelle que soit leur provenance : collecte publique, export de plateforme,
            CSV manuel ou JSON.
          </p>
        </Section>

        <Section id="anonymisation" titre="4. Anonymisation">
          <p>
            Tous les identifiants d'utilisateurs sont pseudonymisés avant toute analyse, au moyen
            d'un HMAC-SHA256 salé, puis remplacés à l'affichage par des étiquettes neutres
            (« Utilisateur 001 », « Utilisateur 002 »…). La table de correspondance reste
            strictement locale et n'est jamais publiée dans <code>public/</code>.
          </p>
          <p>
            Aucun attribut sensible n'est inféré : ni religion, ni origine, ni ethnie, ni
            orientation politique, ni opinion personnelle. L'analyse porte sur des contenus et
            des structures collectives, jamais sur la personnalité des individus.
          </p>
        </Section>

        <Section id="preprocessing" titre="5. Prétraitement">
          <p>
            Le texte brut (<code>raw_text</code>) est conservé et une version nettoyée est
            produite (<code>clean_text</code>). Le prétraitement prend en charge le français,
            l'arabe et les textes mixtes : normalisation Unicode, suppression des diacritiques
            arabes et du tatweel, harmonisation des formes de l'alef, du ya et du ta marbuta,
            suppression des URLs et des mentions, réduction des répétitions de caractères.
          </p>
          <p>
            Les hashtags sont conservés lorsqu'ils portent une valeur analytique : le croisillon
            est retiré mais le terme est maintenu dans le corpus. Mentions, URLs et emojis sont
            extraits séparément. La langue de chaque message est estimée à partir des systèmes
            d'écriture présents (français, arabe, mixte, indéterminé). La darija écrite en
            caractères latins n'est pas traitée de manière spécifique : ce choix est assumé et
            documenté comme une limite.
          </p>
        </Section>

        <Section id="reseau" titre="6. Réseau">
          <p>
            Le réseau est un graphe orienté et pondéré. Chaque nœud est un utilisateur
            pseudonymisé ; chaque lien va de l'auteur d'une interaction vers l'utilisateur visé.
            Les types produisant un lien sont : commentaire, réponse, mention, partage, repost et
            citation. Les publications elles-mêmes ne créent pas de lien mais alimentent le
            compte de messages de leur auteur.
          </p>
          <p>
            Lorsque plusieurs interactions relient les deux mêmes utilisateurs, les poids sont
            agrégés. Sont calculés : nombre de nœuds et de liens, densité, degré moyen, degrés
            entrant et sortant, centralité de degré, centralité d'intermédiarité et composantes
            faiblement connexes. L'intermédiarité est calculée exactement jusqu'à 800 nœuds, puis
            estimée par échantillonnage au-delà.
          </p>
        </Section>

        <Section id="communautes" titre="7. Communautés">
          <p>
            Les communautés sont détectées par l'algorithme de Louvain appliqué à la projection
            non orientée et pondérée du réseau{" "}
            {communautes ? <>(implémentation : {communautes.algorithme})</> : null}. Les
            identifiants sont renumérotés de façon stable, par taille décroissante.
          </p>
          <p>
            Les communautés ne reçoivent que des noms neutres : « Communauté 1 », « Communauté
            2 », etc. Aucune étiquette idéologique n'est générée automatiquement. Une communauté
            est une structure d'interaction, pas un groupe d'opinion : deux utilisateurs peuvent
            être proches dans le graphe parce qu'ils s'affrontent régulièrement. L'interprétation
            idéologique demeure une tâche humaine.
          </p>
        </Section>

        <Section id="modularite" titre="8. Modularité">
          <p>
            La modularité (Newman) mesure l'écart entre la densité des liens observés à
            l'intérieur des communautés et celle attendue dans un graphe aléatoire de même
            distribution de degrés. Elle est calculée sur la projection pondérée, avec la
            partition retenue.
            {communautes ? (
              <>
                {" "}
                Sur le corpus analysé, elle vaut{" "}
                <strong>{decimal(communautes.modularite, 4)}</strong>.
              </>
            ) : null}
          </p>
        </Section>

        <Section id="polarisation" titre="9. Polarisation">
          <p>
            La polarisation structurelle est décrite par des indicateurs simples et vérifiables :
            modularité, nombre d'interactions intra-communautés, nombre d'interactions
            inter-communautés, ratio intra/inter et proportion de liens internes. Les valeurs
            numériques sont toujours affichées.
          </p>
          <p>
            Une lecture qualitative — polarisation faible, modérée ou forte — est proposée à
            partir de seuils conventionnels sur la modularité (inférieure à 0,30 ; entre 0,30 et
            0,50 ; supérieure ou égale à 0,50). <strong>Ces seuils sont indicatifs</strong> : ils
            relèvent d'un usage courant en analyse de réseaux, non d'une métrique validée de la
            polarisation. Aucun « score scientifique » n'est fabriqué.
          </p>
          <Avertissement variante="attention">
            Polarisation, sentiment négatif, colère, toxicité et discours haineux sont des
            dimensions distinctes. Une forte modularité indique une séparation structurelle des
            échanges, pas une hostilité, et réciproquement.
          </Avertissement>
        </Section>

        <Section id="lexique" titre="10. Analyse lexicale">
          <p>
            Pour chaque communauté et chaque plateforme sont extraits : les mots les plus
            fréquents après suppression des mots vides (listes françaises et arabes intégrées au
            projet), les bigrammes, les termes caractéristiques au sens de la pondération TF-IDF
            (scikit-learn) et les hashtags principaux. Les classements sont limités aux vingt
            premiers termes, ramenés à dix dans les fiches de communauté.
          </p>
          <p>
            Le TF-IDF est calculé sur le sous-ensemble sélectionné ; en deçà de trois documents,
            aucun résultat n'est produit plutôt que d'afficher une valeur trompeuse.
          </p>
        </Section>

        <Section id="sentiment" titre="11. Sentiment">
          <p>
            La classification de sentiment (positif, neutre, négatif) est réalisée hors ligne, en
            Python, par un dispositif lexical à base de règles couvrant le français et l'arabe,
            avec gestion de la négation (portée de trois jetons) et de l'intensification. Le
            tableau de bord ne charge aucun modèle d'apprentissage automatique.
          </p>
          <p>
            Aucun modèle multilingue pré-entraîné n'a été retenu, faute de pouvoir en documenter
            honnêtement les performances sur un corpus mêlant français, arabe et darija.
            L'analyse est donc présentée comme <strong>indicative</strong>, et l'architecture
            reste remplaçable : la fonction <code>classer_texte</code> constitue le point
            d'extension unique.
            {sentiment ? (
              <>
                {" "}
                Méthode déclarée : {sentiment.methode.nom}, version {sentiment.methode.version}.
              </>
            ) : null}{" "}
            Aucune mesure de précision, de rappel ou de F1 n'est annoncée : aucune évaluation sur
            corpus annoté n'a été réalisée.
          </p>
        </Section>

        <Section id="emotions" titre="12. Colère et soutien">
          <p>
            Une seconde classification, indépendante de la première, distingue trois catégories :
            colère, soutien ou approbation, autre ou neutre. Elle combine des dictionnaires
            lexicaux et des marqueurs typographiques faibles (points d'exclamation répétés,
            majuscules, quelques emojis), ces derniers étant pondérés faiblement.
          </p>
          <p>
            {emotions?.methode.avertissement ??
              "Il s'agit d'une classification automatique indicative du contenu."}{" "}
            L'objectif est de comparer les communautés entre elles, non de caractériser des
            personnes.
          </p>
        </Section>

        <Section id="haine" titre="13. Discours haineux">
          <p>
            Trois catégories mutuellement exclusives sont distinguées : contenu non haineux,
            contenu toxique ou offensant, et contenu potentiellement haineux. La première
            repose sur un lexique de termes disqualifiant un interlocuteur. La seconde exige une{" "}
            <strong>co-occurrence</strong> entre une désignation collective et une formulation
            d'exclusion, de rejet collectif ou de déshumanisation. Cette règle est volontairement
            conservatrice : la seule mention d'un groupe ne déclenche aucune classification.
          </p>
          <p>
            Un niveau de confiance indicatif est enregistré avec chaque classification. La
            terminologie employée est stricte : on ne parle jamais d'« utilisateur haineux »
            mais de « contenu classifié comme potentiellement haineux ». Cette classification
            signale un signal lexical à vérifier manuellement ; elle ne constitue pas une
            qualification juridique.
            {haine ? (
              <>
                {" "}
                Méthode déclarée : {haine.methode.nom}, version {haine.methode.version}.
              </>
            ) : null}
          </p>
        </Section>

        <Section id="propagation" titre="14. Propagation">
          <p>
            Les cascades sont reconstruites à partir du champ <code>parent_id</code> :
            publication, puis commentaire, réponse, et enfin partage, repost ou citation. Pour
            chaque cascade sont calculés la taille, la profondeur, le nombre de participants, la
            durée, les communautés atteintes, ainsi que les proportions de contenus classés
            négatifs, en colère ou potentiellement haineux.
          </p>
          <p>
            Aucun modèle de diffusion (épidémiologique, processus de Hawkes ou autre) n'est
            estimé : l'analyse reste descriptive. La qualité de la reconstruction dépend
            directement de la présence et de la cohérence du champ <code>parent_id</code> dans
            les données importées.
          </p>
        </Section>

        <Section id="limites" titre="15. Limites">
          <ul className="list-disc space-y-2 pl-5">
            <li>
              Les plateformes concernées n'exposent pas publiquement les interactions
              (commentaires, réponses, partages) sans API autorisée : la collecte automatisée
              est donc, en pratique, impossible dans le cadre éthique retenu.
            </li>
            <li>
              Les classifications de sentiment, de colère/soutien et de toxicité sont
              heuristiques, fondées sur des dictionnaires courts et non exhaustifs. Aucune
              évaluation sur corpus annoté n'a été conduite : aucune performance ne peut être
              annoncée.
            </li>
            <li>
              L'ironie, le sarcasme, l'implicite et les formulations codées échappent à la
              détection. Une citation ou une dénonciation d'un propos haineux peut être classée
              à tort dans une catégorie négative.
            </li>
            <li>
              La darija écrite en caractères latins n'est couverte que partiellement, ce qui
              introduit un biais linguistique en défaveur d'une partie du corpus.
            </li>
            <li>
              La détection de communautés par Louvain est stochastique ; une graine fixe est
              utilisée pour garantir la reproductibilité, mais la partition obtenue n'est pas
              unique.
            </li>
            <li>
              Les seuils d'interprétation de la polarisation sont conventionnels et indicatifs.
            </li>
            <li>
              Aucune inférence causale n'est possible : les résultats décrivent des
              co-occurrences et des structures observées, pas des mécanismes.
            </li>
            {overview?.jeu_de_donnees.synthetique ? (
              <li>
                <strong>
                  Les résultats actuellement affichés proviennent d'un jeu de données
                  synthétique.
                </strong>{" "}
                Ils valident le fonctionnement du dispositif et ne constituent pas des résultats
                empiriques.
              </li>
            ) : null}
          </ul>
        </Section>
      </div>

      <div className="mt-8">
        <Carte>
          <h2 className="text-sm font-semibold text-ardoise-800 dark:text-ardoise-100">
            Reproductibilité
          </h2>
          <p className="mt-2 text-sm text-ardoise-700 dark:text-ardoise-300">
            L'ensemble des résultats présentés dans ce tableau de bord est produit par une
            commande unique, à partir des données présentes dans <code>data/</code> :
          </p>
          <pre className="mt-3 overflow-x-auto rounded-md bg-ardoise-100 p-3 text-xs text-ardoise-800 dark:bg-ardoise-950 dark:text-ardoise-300">
            <code>python analysis/run_analysis.py</code>
          </pre>
          <p className="mt-3 text-sm text-ardoise-700 dark:text-ardoise-300">
            Aucune statistique n'est écrite en dur dans l'interface : toutes les valeurs
            proviennent des fichiers <code>public/data/*.json</code>.
          </p>
        </Carte>
      </div>
    </>
  );
}

function Section({
  id,
  titre,
  children,
}: {
  id: string;
  titre: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-32">
      <Carte>
        <h2 className="mb-3 text-lg font-semibold text-ardoise-900 dark:text-white">{titre}</h2>
        <div className="space-y-3 text-sm leading-relaxed text-ardoise-700 dark:text-ardoise-300">
          {children}
        </div>
      </Carte>
    </section>
  );
}
