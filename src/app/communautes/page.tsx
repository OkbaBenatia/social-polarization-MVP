import type { Metadata } from "next";

import { BandeauJeuDeDonnees } from "@/components/BandeauJeuDeDonnees";
import { GraphiqueBarres } from "@/components/graphiques/GraphiqueBarres";
import { ListeTermes } from "@/components/graphiques/ListeTermes";
import { RepartitionCompacte } from "@/components/graphiques/RepartitionCompacte";
import { Avertissement } from "@/components/ui/Avertissement";
import { Carte, TitreCarte } from "@/components/ui/Carte";
import { EntetePage } from "@/components/ui/EntetePage";
import { EtatVide } from "@/components/ui/EtatVide";
import { KpiCarte } from "@/components/ui/KpiCarte";
import {
  Cellule,
  CorpsTableau,
  EnteteTableau,
  Tableau,
} from "@/components/ui/Tableau";
import { lireCommunautes } from "@/lib/data";
import { decimal, nombre, pourcentage } from "@/lib/format";
import {
  COULEURS_EMOTIONS,
  COULEURS_HAINE,
  COULEURS_SENTIMENT,
  couleurCommunaute,
} from "@/lib/palette";

export const metadata: Metadata = { title: "Communautés" };

export default function PageCommunautes() {
  const donnees = lireCommunautes();

  if (!donnees) {
    return (
      <>
        <EntetePage titre="Communautés" />
        <EtatVide fichier="communities.json" />
      </>
    );
  }

  if (!donnees.communautes.length) {
    return (
      <>
        <EntetePage titre="Communautés" />
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
        <div className="mt-4">
          <EtatVide
            titre="Aucune communauté détectée"
            message={
              donnees.message ||
              "Le réseau ne contient pas suffisamment de liens pour permettre une détection de communautés."
            }
          />
        </div>
      </>
    );
  }

  const { polarisation } = donnees;

  return (
    <>
      <EntetePage
        titre="Communautés"
        description="Groupes d'utilisateurs détectés par l'algorithme de Louvain sur la projection non orientée du réseau. Les communautés portent uniquement des noms neutres : aucune étiquette idéologique n'est générée automatiquement, l'interprétation reste une tâche humaine."
      >
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
      </EntetePage>

      <section className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <KpiCarte libelle="Communautés" valeur={nombre(donnees.nombre_communautes)} />
        <KpiCarte
          libelle="Modularité"
          valeur={decimal(donnees.modularite, 4)}
          precision={donnees.algorithme}
        />
        <KpiCarte libelle="Lecture indicative" valeur={polarisation.interpretation} />
        <KpiCarte
          libelle="Interactions intra"
          valeur={nombre(polarisation.interactions_intra_communautes)}
        />
        <KpiCarte
          libelle="Interactions inter"
          valeur={nombre(polarisation.interactions_inter_communautes)}
        />
        <KpiCarte
          libelle="Part de liens internes"
          valeur={pourcentage(polarisation.part_liens_internes)}
          precision={`ratio ${decimal(polarisation.ratio_intra_inter, 2)}`}
        />
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte description="Taille de chaque communauté en utilisateurs et en messages.">
            Taille des communautés
          </TitreCarte>
          <GraphiqueBarres
            donnees={donnees.communautes.map((communaute) => ({
              nom: communaute.nom,
              utilisateurs: communaute.utilisateurs,
              messages: communaute.messages,
            }))}
            cleAxe="nom"
            series={[
              { cle: "utilisateurs", libelle: "Utilisateurs", couleur: couleurCommunaute(1) },
              { cle: "messages", libelle: "Messages", couleur: couleurCommunaute(2) },
            ]}
          />
        </Carte>

        <Carte>
          <TitreCarte description="Interactions restant à l'intérieur de la communauté, comparées à celles dirigées vers d'autres communautés.">
            Interactions internes et externes
          </TitreCarte>
          <GraphiqueBarres
            donnees={donnees.communautes.map((communaute) => ({
              nom: communaute.nom,
              internes: communaute.interactions_internes,
              externes: communaute.interactions_externes,
            }))}
            cleAxe="nom"
            empile
            series={[
              { cle: "internes", libelle: "Interactions internes", couleur: couleurCommunaute(1) },
              { cle: "externes", libelle: "Interactions externes", couleur: couleurCommunaute(2) },
            ]}
          />
        </Carte>
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-semibold text-ardoise-900 dark:text-white">
          Matrice des interactions entre communautés
        </h2>
        <Tableau>
          <EnteteTableau colonnes={["Communauté émettrice", "Communauté visée", "Interactions"]} />
          <CorpsTableau>
            {donnees.matrice_interactions.map((cellule) => (
              <tr key={`${cellule.source_id}-${cellule.cible_id}`}>
                <Cellule>
                  <span className="flex items-center gap-2">
                    <span
                      aria-hidden="true"
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: couleurCommunaute(cellule.source_id) }}
                    />
                    {cellule.source}
                  </span>
                </Cellule>
                <Cellule>
                  <span className="flex items-center gap-2">
                    <span
                      aria-hidden="true"
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: couleurCommunaute(cellule.cible_id) }}
                    />
                    {cellule.cible}
                    {cellule.source_id === cellule.cible_id ? (
                      <span className="text-xs text-ardoise-500">(interne)</span>
                    ) : null}
                  </span>
                </Cellule>
                <Cellule numerique>{nombre(cellule.interactions)}</Cellule>
              </tr>
            ))}
          </CorpsTableau>
        </Tableau>
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-semibold text-ardoise-900 dark:text-white">
          Fiches détaillées
        </h2>
        <div className="grid gap-4 lg:grid-cols-2">
          {donnees.communautes.map((communaute) => (
            <Carte key={communaute.id}>
              <div className="mb-4 flex items-center gap-2">
                <span
                  aria-hidden="true"
                  className="h-3.5 w-3.5 rounded-full"
                  style={{ backgroundColor: couleurCommunaute(communaute.id) }}
                />
                <h3 className="text-base font-semibold text-ardoise-900 dark:text-white">
                  {communaute.nom}
                </h3>
              </div>

              <dl className="mb-5 grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-3">
                <Mesure terme="Utilisateurs" valeur={nombre(communaute.utilisateurs)} />
                <Mesure terme="Messages" valeur={nombre(communaute.messages)} />
                <Mesure
                  terme="Messages textuels"
                  valeur={nombre(communaute.messages_avec_texte)}
                />
                <Mesure
                  terme="Interactions internes"
                  valeur={nombre(communaute.interactions_internes)}
                />
                <Mesure
                  terme="Interactions externes"
                  valeur={nombre(communaute.interactions_externes)}
                />
                <Mesure
                  terme="Part interne"
                  valeur={pourcentage(communaute.part_interactions_internes)}
                />
              </dl>

              <div className="mb-5 space-y-3">
                <RepartitionCompacte
                  titre="Sentiment (classification indicative)"
                  repartition={communaute.sentiment}
                  couleurs={COULEURS_SENTIMENT}
                />
                <RepartitionCompacte
                  titre="Colère et soutien (classification indicative)"
                  repartition={communaute.emotions}
                  couleurs={COULEURS_EMOTIONS}
                />
                <RepartitionCompacte
                  titre="Toxicité et discours potentiellement haineux (estimation indicative)"
                  repartition={communaute.haine}
                  couleurs={COULEURS_HAINE}
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="mb-2 text-xs font-medium text-ardoise-600 dark:text-ardoise-400">
                    Vocabulaire dominant
                  </p>
                  <ListeTermes
                    termes={communaute.top_mots.map((mot) => ({
                      terme: mot.terme,
                      valeur: mot.occurrences,
                    }))}
                  />
                </div>
                <div>
                  <p className="mb-2 text-xs font-medium text-ardoise-600 dark:text-ardoise-400">
                    Termes caractéristiques (TF-IDF)
                  </p>
                  <ListeTermes
                    termes={communaute.termes_caracteristiques.map((terme) => ({
                      terme: terme.terme,
                      valeur: terme.score,
                    }))}
                    unite="score"
                    vide="Corpus trop réduit pour un calcul TF-IDF."
                  />
                </div>
              </div>

              {communaute.top_hashtags.length ? (
                <div className="mt-4">
                  <p className="mb-2 text-xs font-medium text-ardoise-600 dark:text-ardoise-400">
                    Hashtags principaux
                  </p>
                  <ul className="flex flex-wrap gap-1.5">
                    {communaute.top_hashtags.slice(0, 10).map((hashtag) => (
                      <li
                        key={hashtag.terme}
                        dir="auto"
                        className="rounded-full bg-ardoise-100 px-2.5 py-0.5 text-xs text-ardoise-700 dark:bg-ardoise-800 dark:text-ardoise-300"
                      >
                        {hashtag.terme}{" "}
                        <span className="tabular-nums text-ardoise-500">
                          {hashtag.occurrences}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Carte>
          ))}
        </div>
      </section>

      <Avertissement variante="attention" titre="Lecture des communautés">
        Une communauté est une structure d'interaction, pas un groupe idéologique. La
        proximité de deux utilisateurs dans le graphe traduit une fréquence d'échange, qui
        peut correspondre aussi bien à un accord qu'à une confrontation soutenue.
        {donnees.utilisateurs_non_affectes > 0
          ? ` ${nombre(donnees.utilisateurs_non_affectes)} utilisateur(s) ne sont rattachés à aucune communauté.`
          : ""}
      </Avertissement>
    </>
  );
}

function Mesure({ terme, valeur }: { terme: string; valeur: string }) {
  return (
    <div>
      <dt className="text-xs text-ardoise-500 dark:text-ardoise-400">{terme}</dt>
      <dd className="mt-0.5 font-medium tabular-nums text-ardoise-900 dark:text-ardoise-100">
        {valeur}
      </dd>
    </div>
  );
}
