import { Avertissement } from "./ui/Avertissement";
import type { JeuDeDonnees } from "@/lib/types";

/**
 * Signale explicitement la nature du jeu de données analysé.
 * Les données réelles et synthétiques ne sont jamais confondues.
 */
export function BandeauJeuDeDonnees({ jeu }: { jeu: JeuDeDonnees }) {
  if (jeu.synthetique) {
    return (
      <Avertissement variante="synthetique" titre="Données de démonstration synthétiques">
        {jeu.avertissement} Fichier analysé : <code>{jeu.fichiers.join(", ")}</code>.
      </Avertissement>
    );
  }
  return (
    <Avertissement variante="information" titre="Données réelles importées">
      Les résultats affichés proviennent des données importées au format normalisé (
      <code>{jeu.fichiers.join(", ")}</code>).
    </Avertissement>
  );
}
