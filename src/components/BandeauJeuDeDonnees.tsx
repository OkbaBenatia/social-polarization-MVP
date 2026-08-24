import type { JeuDeDonnees } from "@/lib/types";

/**
 * Signale la nature du jeu de données analysé, de façon discrète et sur une
 * seule ligne. Les données réelles et synthétiques ne sont jamais confondues.
 *
 * Les compteurs de sources sont facultatifs : ils proviennent de `overview.json`
 * lorsque la page en dispose, et ne sont jamais écrits en dur.
 */
export function BandeauJeuDeDonnees({
  jeu,
  sourcesReelles,
  sourcesImportManuel,
}: {
  jeu: JeuDeDonnees;
  sourcesReelles?: number;
  sourcesImportManuel?: number;
}) {
  const compteurs =
    typeof sourcesReelles === "number" && typeof sourcesImportManuel === "number";

  let texte: string;
  if (jeu.synthetique) {
    texte = compteurs
      ? `Aucune donnée réelle importée — ${sourcesImportManuel} source(s) en attente d'import manuel`
      : `Aucune donnée réelle importée — corpus de démonstration (${jeu.fichiers.join(", ")})`;
  } else {
    texte = compteurs
      ? `Données réelles importées — ${sourcesReelles} source(s) analysée(s)`
      : `Données réelles importées (${jeu.fichiers.join(", ")})`;
  }

  return (
    <p
      role="note"
      className="flex items-center gap-2 text-xs text-ardoise-500 dark:text-ardoise-400"
    >
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 shrink-0 rounded-full ${
          jeu.synthetique ? "bg-teal-500" : "bg-ardoise-400"
        }`}
      />
      <span>{texte}</span>
    </p>
  );
}
