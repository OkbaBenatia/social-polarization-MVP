import type { Metadata } from "next";

import { BandeauJeuDeDonnees } from "@/components/BandeauJeuDeDonnees";
import { ExplorateurContenu } from "@/components/ExplorateurContenu";
import { Avertissement } from "@/components/ui/Avertissement";
import { EntetePage } from "@/components/ui/EntetePage";
import { EtatVide } from "@/components/ui/EtatVide";
import { lireContenu } from "@/lib/data";

export const metadata: Metadata = { title: "Analyse du contenu" };

export default function PageContenu() {
  const donnees = lireContenu();

  if (!donnees) {
    return (
      <>
        <EntetePage titre="Analyse du contenu" />
        <EtatVide fichier="content.json" />
      </>
    );
  }

  return (
    <>
      <EntetePage
        titre="Analyse du contenu"
        description="Champs lexicaux observés dans les messages, comparables par communauté et par plateforme. Le prétraitement conserve le texte brut et produit une version nettoyée prenant en charge le français, l'arabe et les textes mixtes."
      >
        <BandeauJeuDeDonnees jeu={donnees.jeu_de_donnees} />
      </EntetePage>

      <section className="mb-6">
        <ExplorateurContenu donnees={donnees} />
      </section>

      <Avertissement variante="information" titre="Méthode">
        {donnees.methode} Les classements sont limités aux {donnees.taille_top} premiers termes.
        La fréquence d'un terme ne présume ni de son intention ni de sa valeur : un même mot
        peut être employé pour affirmer, contester ou citer un propos.
      </Avertissement>
    </>
  );
}
