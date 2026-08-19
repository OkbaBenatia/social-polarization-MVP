import type { Metadata } from "next";

import { BandeauJeuDeDonnees } from "@/components/BandeauJeuDeDonnees";
import { FicheMethode } from "@/components/FicheMethode";
import { ComparaisonCategories } from "@/components/graphiques/ComparaisonCategories";
import { Avertissement } from "@/components/ui/Avertissement";
import { Badge } from "@/components/ui/Badge";
import { Carte, TitreCarte } from "@/components/ui/Carte";
import { EntetePage } from "@/components/ui/EntetePage";
import { EtatVide } from "@/components/ui/EtatVide";
import { KpiCarte } from "@/components/ui/KpiCarte";
import { lireDiscoursHaineux } from "@/lib/data";
import { decimal, nombre, pourcentage } from "@/lib/format";
import { COULEURS_HAINE } from "@/lib/palette";

export const metadata: Metadata = { title: "Discours haineux" };

export default function PageDiscoursHaineux() {
  const donnees = lireDiscoursHaineux();

  if (!donnees) {
    return (
      <>
        <EntetePage titre="Discours haineux" />
        <EtatVide fichier="hate_speech.json" />
      </>
    );
  }

  if (!donnees.messages_analyses) {
    return (
      <>
        <EntetePage titre="Discours haineux" />
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
        <div className="mt-4">
          <EtatVide
            titre="Aucun contenu textuel"
            message={
              donnees.message ||
              "Les interactions importées ne comportent aucun texte exploitable : aucune classification n'a pu être effectuée."
            }
          />
        </div>
      </>
    );
  }

  const parCategorie = Object.fromEntries(
    donnees.global.map((element) => [element.categorie, element]),
  );

  return (
    <>
      <EntetePage
        titre="Toxicité et discours potentiellement haineux"
        description="Estimation indicative portant sur des contenus. Trois catégories distinctes sont retenues : contenu non haineux, contenu toxique ou offensant, et contenu potentiellement haineux — ce dernier étant retenu lorsqu'une désignation collective coexiste avec une formulation d'exclusion ou de rejet."
      >
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
      </EntetePage>

      <Avertissement variante="attention" titre="Terminologie et portée">
        {donnees.avertissement}
      </Avertissement>

      <section className="my-8 grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-5">
        <KpiCarte
          libelle="Messages analysés"
          valeur={nombre(donnees.messages_analyses)}
          precision="messages textuels"
        />
        {donnees.categories.map((categorie) => (
          <KpiCarte
            key={categorie}
            libelle={categorie}
            valeur={nombre(parCategorie[categorie]?.nombre ?? 0)}
            precision={pourcentage(parCategorie[categorie]?.part ?? 0)}
          />
        ))}
        <KpiCarte
          libelle="Confiance moyenne"
          valeur={
            donnees.confiance_disponible ? decimal(donnees.confiance_moyenne, 3) : "non disponible"
          }
          precision="sur les contenus classés"
        />
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte description="RQ6 — Certaines communautés présentent-elles davantage de contenus classifiés comme toxiques ou potentiellement haineux ?">
            Comparaison par communauté
          </TitreCarte>
          <ComparaisonCategories
            lignes={donnees.par_communaute}
            categories={donnees.categories}
            couleurs={COULEURS_HAINE}
            libelleDimension="Communautés"
          />
        </Carte>

        <Carte>
          <TitreCarte description="RQ8 — Comparaison entre plateformes, lorsque les données disponibles la permettent.">
            Comparaison par plateforme
          </TitreCarte>
          <ComparaisonCategories
            lignes={donnees.par_plateforme}
            categories={donnees.categories}
            couleurs={COULEURS_HAINE}
            libelleDimension="Plateformes"
          />
        </Carte>
      </section>

      <section className="mb-8">
        <Carte>
          <TitreCarte description="Répartition par source étudiée. Une source sans interaction importée n'apparaît pas.">
            Comparaison par source
          </TitreCarte>
          <ComparaisonCategories
            lignes={donnees.par_source}
            categories={donnees.categories}
            couleurs={COULEURS_HAINE}
            libelleDimension="Sources"
            hauteur={360}
          />
        </Carte>
      </section>

      {donnees.extraits_publies ? (
        <section className="mb-8">
          <h2 className="mb-2 text-lg font-semibold text-ardoise-900 dark:text-white">
            Exemples de contenus classés
          </h2>
          <p className="mb-4 text-sm text-ardoise-600 dark:text-ardoise-400">
            {donnees.note_extraits}
          </p>
          <div className="space-y-3">
            {donnees.extraits.map((extrait, index) => (
              <Carte key={index}>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Badge ton={extrait.label === "Potentiellement haineux" ? "sombre" : "neutre"}>
                    {extrait.label}
                  </Badge>
                  <Badge ton="neutre">{extrait.communaute}</Badge>
                  <span className="text-xs text-ardoise-500 dark:text-ardoise-400">
                    confiance {decimal(extrait.confiance, 2)}
                  </span>
                </div>
                <p
                  dir="auto"
                  className="texte-mixte text-sm italic text-ardoise-800 dark:text-ardoise-200"
                >
                  « {extrait.extrait} »
                </p>
                <p className="mt-2 font-mono text-xs text-ardoise-500 dark:text-ardoise-500">
                  signaux : {extrait.signaux.join(", ") || "—"}
                </p>
              </Carte>
            ))}
          </div>
        </section>
      ) : (
        <section className="mb-8">
          <Avertissement variante="information" titre="Extraits de contenu">
            {donnees.note_extraits}
          </Avertissement>
        </section>
      )}

      <section className="grid gap-4 lg:grid-cols-2">
        <FicheMethode methode={donnees.methode} />
        <Carte>
          <TitreCarte description="Distinctions conceptuelles maintenues tout au long de l'analyse.">
            Ce que cette page ne dit pas
          </TitreCarte>
          <ul className="list-disc space-y-2 pl-5 text-sm text-ardoise-700 dark:text-ardoise-300">
            <li>
              Elle ne qualifie aucun utilisateur : seuls des contenus sont classés, jamais des
              personnes.
            </li>
            <li>
              Un sentiment négatif n'est pas de la colère, la colère n'est pas de la toxicité, et
              la toxicité n'est pas du discours haineux.
            </li>
            <li>
              La classification « potentiellement haineux » signale un signal lexical à vérifier
              manuellement ; elle ne constitue pas une qualification juridique.
            </li>
            <li>
              Aucune inférence n'est faite sur la religion, l'origine, l'ethnie ou l'orientation
              politique des personnes.
            </li>
            <li>
              Une citation ou une dénonciation d'un propos haineux peut être classée à tort dans
              une catégorie négative.
            </li>
          </ul>
        </Carte>
      </section>
    </>
  );
}
