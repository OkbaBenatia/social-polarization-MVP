import { BandeauJeuDeDonnees } from "@/components/BandeauJeuDeDonnees";
import { GraphiqueBarres } from "@/components/graphiques/GraphiqueBarres";
import { GraphiqueCamembert } from "@/components/graphiques/GraphiqueCamembert";
import { GraphiqueLignes } from "@/components/graphiques/GraphiqueLignes";
import { Avertissement } from "@/components/ui/Avertissement";
import { Carte, TitreCarte } from "@/components/ui/Carte";
import { EntetePage } from "@/components/ui/EntetePage";
import { EtatVide } from "@/components/ui/EtatVide";
import { KpiCarte } from "@/components/ui/KpiCarte";
import { lireOverview } from "@/lib/data";
import { decimal, nombre, pourcentage } from "@/lib/format";
import {
  COULEURS_EMOTIONS,
  COULEURS_HAINE,
  COULEURS_PLATEFORMES,
  COULEURS_SENTIMENT,
  couleurCategorie,
  couleurCommunaute,
} from "@/lib/palette";

export default function PageVueDEnsemble() {
  const donnees = lireOverview();

  if (!donnees) {
    return (
      <>
        <EntetePage titre="Vue d'ensemble" />
        <EtatVide fichier="overview.json" />
      </>
    );
  }

  const { kpi, polarisation, reseau, qualite_donnees: qualite } = donnees;

  return (
    <>
      <EntetePage
        titre="Vue d'ensemble"
        description="Synthèse des indicateurs calculés par le pipeline d'analyse : volume de données, structure du réseau, communautés détectées, polarisation structurelle et classification indicative des contenus."
      >
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
      </EntetePage>

      <section aria-label="Indicateurs clés" className="mb-8">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-7">
          <KpiCarte
            libelle="Sources analysées"
            valeur={`${nombre(kpi.sources_avec_donnees)} / ${nombre(kpi.sources_declarees)}`}
            precision="sources avec données importées"
          />
          <KpiCarte libelle="Publications" valeur={nombre(kpi.publications)} />
          <KpiCarte libelle="Utilisateurs" valeur={nombre(kpi.utilisateurs)} precision="pseudonymisés" />
          <KpiCarte libelle="Interactions" valeur={nombre(kpi.interactions)} />
          <KpiCarte libelle="Communautés" valeur={nombre(kpi.communautes)} precision="détectées (Louvain)" />
          <KpiCarte
            libelle="Polarisation"
            valeur={decimal(kpi.modularite, 3)}
            precision={`${kpi.polarisation} (indicatif)`}
          />
          <KpiCarte
            libelle="Contenus potentiellement haineux"
            valeur={nombre(kpi.contenus_potentiellement_haineux)}
            precision={`sur ${nombre(kpi.messages_avec_texte)} messages textuels`}
          />
        </div>
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-3">
        <Carte>
          <TitreCarte description="Nombre d'interactions importées par plateforme.">
            Répartition par plateforme
          </TitreCarte>
          <GraphiqueCamembert
            donnees={donnees.repartition_plateformes.map((element) => ({
              nom: element.libelle,
              valeur: element.interactions,
              couleur: COULEURS_PLATEFORMES[element.plateforme] ?? "#64748b",
            }))}
          />
        </Carte>

        <Carte>
          <TitreCarte description="Classification automatique indicative des messages textuels.">
            Sentiment global
          </TitreCarte>
          <GraphiqueCamembert
            donnees={donnees.sentiment_global.map((element, index) => ({
              nom: element.categorie,
              valeur: element.nombre,
              couleur: couleurCategorie(element.categorie, COULEURS_SENTIMENT, index),
            }))}
          />
        </Carte>

        <Carte>
          <TitreCarte description="Classification automatique indicative du contenu, et non de l'état psychologique des personnes.">
            Colère et soutien
          </TitreCarte>
          <GraphiqueCamembert
            donnees={donnees.emotions_globales.map((element, index) => ({
              nom: element.categorie,
              valeur: element.nombre,
              couleur: couleurCategorie(element.categorie, COULEURS_EMOTIONS, index),
            }))}
          />
        </Carte>
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte description="Nombre d'utilisateurs et de messages par communauté détectée.">
            Distribution des communautés
          </TitreCarte>
          <GraphiqueBarres
            donnees={donnees.distribution_communautes.map((element) => ({
              communaute: element.communaute,
              utilisateurs: element.utilisateurs,
              messages: element.messages,
            }))}
            cleAxe="communaute"
            series={[
              { cle: "utilisateurs", libelle: "Utilisateurs", couleur: couleurCommunaute(1) },
              { cle: "messages", libelle: "Messages", couleur: couleurCommunaute(2) },
            ]}
          />
        </Carte>

        <Carte>
          <TitreCarte description="Contenus classifiés comme toxiques ou potentiellement haineux — estimation indicative.">
            Toxicité et discours potentiellement haineux
          </TitreCarte>
          <GraphiqueBarres
            donnees={donnees.haine_globale.map((element) => ({
              categorie: element.categorie,
              messages: element.nombre,
            }))}
            cleAxe="categorie"
            series={[
              { cle: "messages", libelle: "Messages", couleur: COULEURS_HAINE["Toxique / offensant"] },
            ]}
            hauteur={280}
          />
        </Carte>
      </section>

      <section className="mb-8">
        <Carte>
          <TitreCarte description="Volume quotidien d'interactions et de contenus classifiés. Cette courbe dépend de la disponibilité des horodatages dans les données importées.">
            Évolution temporelle
          </TitreCarte>
          <GraphiqueLignes
            donnees={donnees.evolution_temporelle}
            cleAxe="date"
            series={[
              { cle: "interactions", libelle: "Interactions", couleur: "#475569" },
              { cle: "negatif", libelle: "Sentiment négatif", couleur: "#0d9488" },
              { cle: "colere", libelle: "Colère", couleur: "#94a3b8" },
              {
                cle: "potentiellement_haineux",
                libelle: "Potentiellement haineux",
                couleur: "#0f172a",
              },
            ]}
          />
        </Carte>
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte description="Indicateurs structurels du réseau d'interactions entre utilisateurs.">
            Structure du réseau
          </TitreCarte>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <Ligne terme="Nœuds (utilisateurs)" valeur={nombre(reseau.noeuds)} />
            <Ligne terme="Liens (paires en interaction)" valeur={nombre(reseau.liens)} />
            <Ligne terme="Interactions agrégées" valeur={nombre(reseau.poids_total)} />
            <Ligne terme="Densité" valeur={decimal(reseau.densite, 5)} />
            <Ligne terme="Degré moyen" valeur={decimal(reseau.degre_moyen, 2)} />
            <Ligne terme="Réciprocité" valeur={decimal(reseau.reciprocite, 3)} />
            <Ligne terme="Composantes faibles" valeur={nombre(reseau.composantes_faibles)} />
            <Ligne
              terme="Composante principale"
              valeur={`${nombre(reseau.taille_composante_principale)} (${pourcentage(
                reseau.part_composante_principale,
              )})`}
            />
          </dl>
        </Carte>

        <Carte>
          <TitreCarte description="Mesures simples et transparentes. Les seuils d'interprétation sont indicatifs.">
            Polarisation structurelle
          </TitreCarte>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <Ligne terme="Modularité" valeur={decimal(polarisation.modularite, 4)} />
            <Ligne terme="Lecture indicative" valeur={polarisation.interpretation} />
            <Ligne
              terme="Interactions intra-communautés"
              valeur={nombre(polarisation.interactions_intra_communautes)}
            />
            <Ligne
              terme="Interactions inter-communautés"
              valeur={nombre(polarisation.interactions_inter_communautes)}
            />
            <Ligne
              terme="Part de liens internes"
              valeur={pourcentage(polarisation.part_liens_internes)}
            />
            <Ligne
              terme="Ratio intra / inter"
              valeur={decimal(polarisation.ratio_intra_inter, 2)}
            />
          </dl>
          <p className="mt-4 text-xs leading-relaxed text-ardoise-500 dark:text-ardoise-400">
            {polarisation.avertissement}
          </p>
        </Carte>
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte description="Contrôles appliqués lors du chargement du jeu de données.">
            Qualité des données
          </TitreCarte>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <Ligne terme="Lignes ignorées" valeur={nombre(qualite.lignes_ignorees)} />
            <Ligne terme="Doublons supprimés" valeur={nombre(qualite.doublons_supprimes)} />
            <Ligne terme="Horodatages invalides" valeur={nombre(qualite.horodatages_invalides)} />
            <Ligne terme="Messages sans texte" valeur={nombre(qualite.messages_sans_texte)} />
            <Ligne
              terme="Types d'interaction non reconnus"
              valeur={qualite.types_inconnus.length ? qualite.types_inconnus.join(", ") : "aucun"}
            />
          </dl>
        </Carte>

        <Carte>
          <TitreCarte description="Questions structurant l'étude.">
            Questions de recherche
          </TitreCarte>
          <ul className="space-y-2 text-sm text-ardoise-700 dark:text-ardoise-300">
            {donnees.questions_recherche.map((question) => (
              <li key={question} className="leading-relaxed">
                {question}
              </li>
            ))}
          </ul>
        </Carte>
      </section>

      <Avertissement variante="attention" titre="Précaution d'interprétation">
        Polarisation, sentiment négatif, colère, toxicité et discours haineux sont des
        dimensions distinctes : elles ne doivent jamais être confondues ni additionnées. Les
        classifications automatiques présentées ici sont indicatives et n'ont fait l'objet
        d'aucune évaluation sur corpus annoté.
      </Avertissement>
    </>
  );
}

function Ligne({ terme, valeur }: { terme: string; valeur: string }) {
  return (
    <div>
      <dt className="text-xs text-ardoise-500 dark:text-ardoise-400">{terme}</dt>
      <dd className="mt-0.5 font-medium tabular-nums text-ardoise-900 dark:text-ardoise-100">
        {valeur}
      </dd>
    </div>
  );
}
