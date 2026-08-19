import type { Metadata } from "next";

import { ArbreCascade } from "@/components/ArbreCascade";
import { BandeauJeuDeDonnees } from "@/components/BandeauJeuDeDonnees";
import { GraphiqueBarres } from "@/components/graphiques/GraphiqueBarres";
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
import { lirePropagation } from "@/lib/data";
import { duree, nombre, nomPlateforme, pourcentage } from "@/lib/format";

export const metadata: Metadata = { title: "Propagation" };

export default function PagePropagation() {
  const donnees = lirePropagation();

  if (!donnees) {
    return (
      <>
        <EntetePage titre="Propagation" />
        <EtatVide fichier="propagation.json" />
      </>
    );
  }

  if (!donnees.nombre_cascades) {
    return (
      <>
        <EntetePage titre="Propagation" />
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
        <div className="mt-4">
          <EtatVide
            titre="Aucune cascade reconstruite"
            message={
              donnees.message ||
              "Les données importées ne comportent pas de relations parent-enfant exploitables (colonne parent_id) : aucune cascade ne peut être reconstruite."
            }
          />
        </div>
      </>
    );
  }

  const { statistiques } = donnees;
  const principales = donnees.cascades.slice(0, 12);

  return (
    <>
      <EntetePage
        titre="Propagation"
        description="Reconstruction descriptive des cascades d'interactions à partir des relations parent-enfant : publication, commentaire, réponse, puis partage, repost ou citation. Aucun modèle de diffusion n'est estimé."
      >
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
      </EntetePage>

      <section className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <KpiCarte libelle="Cascades" valeur={nombre(statistiques.nombre_cascades)} />
        <KpiCarte
          libelle="Taille moyenne"
          valeur={nombre(statistiques.taille_moyenne)}
          precision={`maximum ${nombre(statistiques.taille_maximale)}`}
        />
        <KpiCarte
          libelle="Profondeur moyenne"
          valeur={nombre(statistiques.profondeur_moyenne)}
          precision={`maximum ${nombre(statistiques.profondeur_maximale)}`}
        />
        <KpiCarte libelle="Durée moyenne" valeur={duree(statistiques.duree_moyenne_minutes)} />
        <KpiCarte
          libelle="Cascades multi-communautés"
          valeur={nombre(statistiques.cascades_multi_communautes)}
          precision={`sur ${nombre(statistiques.nombre_cascades)}`}
        />
        <KpiCarte
          libelle="Communautés atteintes (max.)"
          valeur={nombre(
            Math.max(...donnees.cascades.map((cascade) => cascade.nombre_communautes_atteintes)),
          )}
        />
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte description="Taille et profondeur des principales cascades observées.">
            Ampleur des cascades
          </TitreCarte>
          <GraphiqueBarres
            donnees={principales.map((cascade) => ({
              cascade: cascade.cascade_id,
              taille: cascade.taille,
              participants: cascade.participants,
            }))}
            cleAxe="cascade"
            series={[
              { cle: "taille", libelle: "Interactions", couleur: "#475569" },
              { cle: "participants", libelle: "Participants", couleur: "#0d9488" },
            ]}
          />
        </Carte>

        <Carte>
          <TitreCarte description="Part des contenus classés dans chaque cascade — classification indicative.">
            Contenus classés par cascade
          </TitreCarte>
          <GraphiqueBarres
            donnees={principales.map((cascade) => ({
              cascade: cascade.cascade_id,
              negatif: cascade.taux_negatif,
              colere: cascade.taux_colere,
              haineux: cascade.taux_potentiellement_haineux,
            }))}
            cleAxe="cascade"
            series={[
              { cle: "negatif", libelle: "Sentiment négatif", couleur: "#94a3b8" },
              { cle: "colere", libelle: "Colère", couleur: "#475569" },
              { cle: "haineux", libelle: "Potentiellement haineux", couleur: "#0f172a" },
            ]}
            format="pourcentage"
          />
        </Carte>
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-semibold text-ardoise-900 dark:text-white">
          Cascades principales
        </h2>
        <Tableau>
          <EnteteTableau
            colonnes={[
              "Cascade",
              "Source",
              "Plateforme",
              "Taille",
              "Profondeur",
              "Participants",
              "Durée",
              "Communautés atteintes",
              "Négatif",
              "Colère",
              "Potentiellement haineux",
            ]}
          />
          <CorpsTableau>
            {principales.map((cascade) => (
              <tr key={cascade.cascade_id}>
                <Cellule className="font-mono text-xs">{cascade.cascade_id}</Cellule>
                <Cellule className="font-mono text-xs">{cascade.source_id}</Cellule>
                <Cellule>{nomPlateforme(cascade.plateforme)}</Cellule>
                <Cellule numerique>{nombre(cascade.taille)}</Cellule>
                <Cellule numerique>{nombre(cascade.profondeur)}</Cellule>
                <Cellule numerique>{nombre(cascade.participants)}</Cellule>
                <Cellule numerique>{duree(cascade.duree_minutes)}</Cellule>
                <Cellule className="text-xs">
                  {cascade.communautes_atteintes.join(", ") || "—"}
                </Cellule>
                <Cellule numerique>{pourcentage(cascade.taux_negatif, 0)}</Cellule>
                <Cellule numerique>{pourcentage(cascade.taux_colere, 0)}</Cellule>
                <Cellule numerique>
                  {pourcentage(cascade.taux_potentiellement_haineux, 0)}
                </Cellule>
              </tr>
            ))}
          </CorpsTableau>
        </Tableau>
      </section>

      <section className="mb-8">
        <Carte>
          <TitreCarte description="Déploiement d'une cascade par niveau de profondeur : publication, commentaires, puis réponses successives.">
            Structure d'une cascade
          </TitreCarte>
          <ArbreCascade
            cascades={donnees.cascades}
            arbres={donnees.arbres}
            noeudsMax={donnees.noeuds_max_par_arbre}
          />
        </Carte>
      </section>

      <Avertissement variante="information" titre="Méthode">
        {donnees.methode} La qualité de la reconstruction dépend directement de la présence et
        de la cohérence du champ <code>parent_id</code> dans les données importées : lorsque
        ce champ est absent, la profondeur observée est nulle.
      </Avertissement>
    </>
  );
}
