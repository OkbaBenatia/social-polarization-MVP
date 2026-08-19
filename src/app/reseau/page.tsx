import type { Metadata } from "next";

import { BandeauJeuDeDonnees } from "@/components/BandeauJeuDeDonnees";
import { ReseauCytoscape } from "@/components/ReseauCytoscape";
import { Carte, TitreCarte } from "@/components/ui/Carte";
import { EntetePage } from "@/components/ui/EntetePage";
import { EtatVide } from "@/components/ui/EtatVide";
import { lireReseau } from "@/lib/data";
import { decimal, nombre, pourcentage } from "@/lib/format";

export const metadata: Metadata = { title: "Réseau" };

export default function PageReseau() {
  const donnees = lireReseau();

  if (!donnees) {
    return (
      <>
        <EntetePage titre="Réseau" />
        <EtatVide fichier="network.json" />
      </>
    );
  }

  if (!donnees.liens_total) {
    return (
      <>
        <EntetePage titre="Réseau" />
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
        <div className="mt-4">
          <EtatVide
            titre="Aucun lien d'interaction"
            message={
              donnees.message ||
              "Le jeu de données ne contient aucune interaction reliant deux utilisateurs : le réseau ne peut pas être construit."
            }
          />
        </div>
      </>
    );
  }

  const { metriques } = donnees;

  return (
    <>
      <EntetePage
        titre="Réseau d'interactions"
        description="Graphe orienté et pondéré des interactions entre utilisateurs pseudonymisés. Un lien va de l'auteur d'une interaction vers l'utilisateur visé ; son poids agrège toutes les interactions observées entre ces deux comptes."
      >
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
      </EntetePage>

      <section className="mb-6">
        <ReseauCytoscape donnees={donnees} />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte description="Mesures calculées sur l'ensemble du réseau, avant troncature d'affichage.">
            Métriques structurelles
          </TitreCarte>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <Mesure terme="Nœuds" valeur={nombre(metriques.noeuds)} />
            <Mesure terme="Liens" valeur={nombre(metriques.liens)} />
            <Mesure terme="Interactions agrégées" valeur={nombre(metriques.poids_total)} />
            <Mesure terme="Densité" valeur={decimal(metriques.densite, 5)} />
            <Mesure terme="Degré moyen" valeur={decimal(metriques.degre_moyen, 2)} />
            <Mesure
              terme="Degré entrant moyen"
              valeur={decimal(metriques.degre_entrant_moyen, 2)}
            />
            <Mesure
              terme="Degré sortant moyen"
              valeur={decimal(metriques.degre_sortant_moyen, 2)}
            />
            <Mesure terme="Réciprocité" valeur={decimal(metriques.reciprocite, 3)} />
            <Mesure
              terme="Composantes faiblement connexes"
              valeur={nombre(metriques.composantes_faibles)}
            />
            <Mesure
              terme="Composante principale"
              valeur={`${nombre(metriques.taille_composante_principale)} (${pourcentage(
                metriques.part_composante_principale,
              )})`}
            />
          </dl>
          <p className="mt-4 text-xs leading-relaxed text-ardoise-500 dark:text-ardoise-400">
            La centralité d'intermédiarité est calculée{" "}
            {metriques.intermediarite_exacte
              ? "de manière exacte sur l'ensemble des nœuds."
              : "par échantillonnage, le réseau dépassant le seuil de calcul exact."}
          </p>
        </Carte>

        <Carte>
          <TitreCarte description="Utilisateurs les plus centraux du réseau, par centralité de degré.">
            Utilisateurs les plus centraux
          </TitreCarte>
          <ol className="space-y-2 text-sm">
            {donnees.noeuds.slice(0, 10).map((noeud, index) => (
              <li
                key={noeud.id}
                className="flex items-baseline justify-between gap-3 border-b border-ardoise-100 pb-1.5 last:border-0 dark:border-ardoise-800"
              >
                <span className="text-ardoise-800 dark:text-ardoise-200">
                  <span className="mr-2 text-xs tabular-nums text-ardoise-400">{index + 1}.</span>
                  {noeud.label}
                  <span className="ml-2 text-xs text-ardoise-500">{noeud.communaute}</span>
                </span>
                <span className="shrink-0 tabular-nums text-xs text-ardoise-500 dark:text-ardoise-400">
                  degré {nombre(noeud.degre)} · centralité{" "}
                  {decimal(noeud.centralite_degre, 3)}
                </span>
              </li>
            ))}
          </ol>
        </Carte>
      </section>
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
