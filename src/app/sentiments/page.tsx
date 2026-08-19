import type { Metadata } from "next";

import { BandeauJeuDeDonnees } from "@/components/BandeauJeuDeDonnees";
import { FicheMethode } from "@/components/FicheMethode";
import { ComparaisonCategories } from "@/components/graphiques/ComparaisonCategories";
import { GraphiqueCamembert } from "@/components/graphiques/GraphiqueCamembert";
import { Avertissement } from "@/components/ui/Avertissement";
import { Carte, TitreCarte } from "@/components/ui/Carte";
import { EntetePage } from "@/components/ui/EntetePage";
import { EtatVide } from "@/components/ui/EtatVide";
import { lireEmotions, lireSentiment } from "@/lib/data";
import { nombre, pourcentage } from "@/lib/format";
import { COULEURS_EMOTIONS, COULEURS_SENTIMENT, couleurCategorie } from "@/lib/palette";

export const metadata: Metadata = { title: "Sentiments et émotions" };

export default function PageSentiments() {
  const sentiment = lireSentiment();
  const emotions = lireEmotions();

  if (!sentiment || !emotions) {
    return (
      <>
        <EntetePage titre="Sentiments et émotions" />
        <EtatVide fichier="sentiment.json / emotions.json" />
      </>
    );
  }

  if (!sentiment.messages_analyses) {
    return (
      <>
        <EntetePage titre="Sentiments et émotions" />
        <BandeauJeuDeDonnees jeu={sentiment.jeu_de_donnees} />
        <div className="mt-4">
          <EtatVide
            titre="Aucun contenu textuel"
            message={
              sentiment.message ||
              "Les interactions importées ne comportent aucun texte exploitable : les analyses de sentiment et d'émotion ne peuvent pas être menées."
            }
          />
        </div>
      </>
    );
  }

  return (
    <>
      <EntetePage
        titre="Sentiments et émotions"
        description="Classification automatique indicative des messages textuels selon deux dimensions distinctes : la polarité du sentiment (positif, neutre, négatif) et l'expression de colère ou de soutien. Ces deux dimensions ne se confondent pas."
      >
        <BandeauJeuDeDonnees jeu={sentiment.jeu_de_donnees} />
      </EntetePage>

      <Avertissement variante="attention" titre="Précaution d'interprétation">
        {sentiment.avertissement} {emotions.avertissement}
      </Avertissement>

      <section className="my-8 grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte
            description={`Répartition sur ${nombre(sentiment.messages_analyses)} messages textuels.`}
          >
            Sentiment global
          </TitreCarte>
          <GraphiqueCamembert
            donnees={sentiment.global.map((element, index) => ({
              nom: element.categorie,
              valeur: element.nombre,
              couleur: couleurCategorie(element.categorie, COULEURS_SENTIMENT, index),
            }))}
          />
          <ul className="mt-3 space-y-1 text-sm text-ardoise-700 dark:text-ardoise-300">
            {sentiment.global.map((element) => (
              <li key={element.categorie} className="flex justify-between">
                <span>{element.categorie}</span>
                <span className="tabular-nums">
                  {nombre(element.nombre)} · {pourcentage(element.part)}
                </span>
              </li>
            ))}
          </ul>
        </Carte>

        <Carte>
          <TitreCarte
            description={`Répartition sur ${nombre(emotions.messages_analyses)} messages textuels.`}
          >
            Colère et soutien
          </TitreCarte>
          <GraphiqueCamembert
            donnees={emotions.global.map((element, index) => ({
              nom: element.categorie,
              valeur: element.nombre,
              couleur: couleurCategorie(element.categorie, COULEURS_EMOTIONS, index),
            }))}
          />
          <ul className="mt-3 space-y-1 text-sm text-ardoise-700 dark:text-ardoise-300">
            {emotions.global.map((element) => (
              <li key={element.categorie} className="flex justify-between">
                <span>{element.categorie}</span>
                <span className="tabular-nums">
                  {nombre(element.nombre)} · {pourcentage(element.part)}
                </span>
              </li>
            ))}
          </ul>
        </Carte>
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-2">
        <Carte>
          <TitreCarte description="RQ4 — Certaines communautés présentent-elles davantage de sentiment négatif ?">
            Sentiment par communauté
          </TitreCarte>
          <ComparaisonCategories
            lignes={sentiment.par_communaute}
            categories={sentiment.categories}
            couleurs={COULEURS_SENTIMENT}
            libelleDimension="Communautés"
          />
        </Carte>

        <Carte>
          <TitreCarte description="RQ5 — Certaines communautés expriment-elles davantage de colère ou de soutien ?">
            Colère et soutien par communauté
          </TitreCarte>
          <ComparaisonCategories
            lignes={emotions.par_communaute}
            categories={emotions.categories}
            couleurs={COULEURS_EMOTIONS}
            libelleDimension="Communautés"
          />
        </Carte>

        <Carte>
          <TitreCarte description="RQ8 — Comparaison entre plateformes, lorsque les données disponibles la permettent.">
            Sentiment par plateforme
          </TitreCarte>
          <ComparaisonCategories
            lignes={sentiment.par_plateforme}
            categories={sentiment.categories}
            couleurs={COULEURS_SENTIMENT}
            libelleDimension="Plateformes"
          />
        </Carte>

        <Carte>
          <TitreCarte description="RQ8 — Comparaison entre plateformes, lorsque les données disponibles la permettent.">
            Colère et soutien par plateforme
          </TitreCarte>
          <ComparaisonCategories
            lignes={emotions.par_plateforme}
            categories={emotions.categories}
            couleurs={COULEURS_EMOTIONS}
            libelleDimension="Plateformes"
          />
        </Carte>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <FicheMethode methode={sentiment.methode} />
        <FicheMethode methode={emotions.methode} />
      </section>
    </>
  );
}
