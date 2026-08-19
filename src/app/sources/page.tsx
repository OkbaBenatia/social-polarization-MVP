import type { Metadata } from "next";

import { BandeauJeuDeDonnees } from "@/components/BandeauJeuDeDonnees";
import { Avertissement } from "@/components/ui/Avertissement";
import { Badge, tonStatut } from "@/components/ui/Badge";
import { Carte, TitreCarte } from "@/components/ui/Carte";
import { EntetePage } from "@/components/ui/EntetePage";
import { EtatVide } from "@/components/ui/EtatVide";
import {
  Cellule,
  CorpsTableau,
  EnteteTableau,
  Tableau,
} from "@/components/ui/Tableau";
import { lireSources } from "@/lib/data";
import { nombre, nomPlateforme } from "@/lib/format";

export const metadata: Metadata = { title: "Sources étudiées" };

export default function PageSources() {
  const donnees = lireSources();

  if (!donnees) {
    return (
      <>
        <EntetePage titre="Sources étudiées" />
        <EtatVide fichier="sources.json" />
      </>
    );
  }

  return (
    <>
      <EntetePage
        titre="Sources étudiées"
        description="Liste des publications réelles constituant les cas d'étude initiaux, avec le statut de collecte effectivement obtenu pour chacune. Une source n'est jamais déclarée analysée si ses données n'ont pas été réellement récupérées ou importées."
      >
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
      </EntetePage>

      <section className="mb-6">
        <Tableau>
          <EnteteTableau
            colonnes={[
              "Plateforme",
              "Identifiant",
              "URL",
              "Statut",
              "Interactions",
              "Publications",
              "Méthode d'acquisition",
            ]}
          />
          <CorpsTableau>
            {donnees.sources.map((source) => (
              <tr key={source.source_id}>
                <Cellule>{nomPlateforme(source.plateforme)}</Cellule>
                <Cellule className="font-mono text-xs">{source.source_id}</Cellule>
                <Cellule>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer nofollow"
                    className="break-all text-teal-700 underline-offset-2 hover:underline dark:text-teal-400"
                  >
                    {source.url}
                  </a>
                </Cellule>
                <Cellule>
                  <Badge ton={tonStatut(source.statut)}>{source.statut}</Badge>
                </Cellule>
                <Cellule numerique>{nombre(source.interactions)}</Cellule>
                <Cellule numerique>{nombre(source.publications)}</Cellule>
                <Cellule className="text-xs">{source.methode_acquisition}</Cellule>
              </tr>
            ))}
          </CorpsTableau>
        </Tableau>
      </section>

      <section className="mb-6 grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte description="Signification des statuts affichés ci-dessus.">
            Statuts de collecte
          </TitreCarte>
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="font-medium text-ardoise-800 dark:text-ardoise-200">
                Données disponibles
              </dt>
              <dd className="text-ardoise-600 dark:text-ardoise-400">
                Des interactions réelles ont été importées au format normalisé pour cette source.
              </dd>
            </div>
            <div>
              <dt className="font-medium text-ardoise-800 dark:text-ardoise-200">Accès partiel</dt>
              <dd className="text-ardoise-600 dark:text-ardoise-400">
                Seules des métadonnées publiques ont pu être lues ; aucune interaction n'a été
                récupérée.
              </dd>
            </div>
            <div>
              <dt className="font-medium text-ardoise-800 dark:text-ardoise-200">
                Import manuel requis
              </dt>
              <dd className="text-ardoise-600 dark:text-ardoise-400">
                La collecte automatique n'a rien produit d'exploitable : les données doivent être
                importées via <code>data/import_template.csv</code>.
              </dd>
            </div>
            <div>
              <dt className="font-medium text-ardoise-800 dark:text-ardoise-200">
                Données de démonstration
              </dt>
              <dd className="text-ardoise-600 dark:text-ardoise-400">
                Les interactions rattachées à cette source proviennent du jeu synthétique de
                démonstration, et non de la plateforme.
              </dd>
            </div>
          </dl>
        </Carte>

        <Carte>
          <TitreCarte description="Règles appliquées lors de la tentative de collecte publique.">
            Cadre de collecte
          </TitreCarte>
          <ul className="list-disc space-y-2 pl-5 text-sm text-ardoise-700 dark:text-ardoise-300">
            {donnees.regles_collecte.map((regle) => (
              <li key={regle}>{regle}</li>
            ))}
          </ul>
        </Carte>
      </section>

      <section className="mb-6">
        <h2 className="mb-3 text-lg font-semibold text-ardoise-900 dark:text-white">
          Détail de la collecte par source
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          {donnees.sources.map((source) => (
            <Carte key={source.source_id}>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Badge ton="neutre">{nomPlateforme(source.plateforme)}</Badge>
                <Badge ton={tonStatut(source.statut)}>{source.statut}</Badge>
                <span className="font-mono text-xs text-ardoise-500">{source.source_id}</span>
              </div>
              <dl className="space-y-2 text-sm">
                <div className="flex gap-2">
                  <dt className="shrink-0 text-ardoise-500 dark:text-ardoise-400">
                    Collecte tentée :
                  </dt>
                  <dd className="text-ardoise-800 dark:text-ardoise-200">
                    {source.collecte_tentee ? "oui" : "non"}
                  </dd>
                </div>
                <div className="flex gap-2">
                  <dt className="shrink-0 text-ardoise-500 dark:text-ardoise-400">
                    Réponse HTTP :
                  </dt>
                  <dd className="text-ardoise-800 dark:text-ardoise-200">
                    {source.http_status ?? "aucune réponse obtenue"}
                  </dd>
                </div>
                {source.robots_txt ? (
                  <div>
                    <dt className="text-ardoise-500 dark:text-ardoise-400">robots.txt :</dt>
                    <dd className="mt-0.5 text-xs leading-relaxed text-ardoise-700 dark:text-ardoise-300">
                      {source.robots_txt}
                    </dd>
                  </div>
                ) : null}
                {Object.keys(source.metadonnees_publiques).length ? (
                  <div>
                    <dt className="text-ardoise-500 dark:text-ardoise-400">
                      Métadonnées publiques lues :
                    </dt>
                    <dd className="mt-0.5 space-y-1 text-xs text-ardoise-700 dark:text-ardoise-300">
                      {Object.entries(source.metadonnees_publiques).map(([cle, valeur]) => (
                        <p key={cle} dir="auto">
                          <span className="font-mono text-ardoise-500">{cle}</span> : {valeur}
                        </p>
                      ))}
                    </dd>
                  </div>
                ) : null}
                {source.limites.length ? (
                  <div>
                    <dt className="text-ardoise-500 dark:text-ardoise-400">
                      Limites constatées :
                    </dt>
                    <dd>
                      <ul className="mt-1 list-disc space-y-1 pl-5 text-xs leading-relaxed text-ardoise-700 dark:text-ardoise-300">
                        {source.limites.map((limite, index) => (
                          <li key={index}>{limite}</li>
                        ))}
                      </ul>
                    </dd>
                  </div>
                ) : null}
              </dl>
            </Carte>
          ))}
        </div>
      </section>

      <Avertissement variante="attention" titre="Périmètre réellement couvert">
        Aucune protection technique n'a été contournée : ni authentification, ni CAPTCHA, ni
        limitation d'API. Lorsqu'une plateforme n'expose pas publiquement les interactions,
        la source reste en attente d'un import manuel et n'est pas comptabilisée comme
        analysée.
      </Avertissement>
    </>
  );
}
