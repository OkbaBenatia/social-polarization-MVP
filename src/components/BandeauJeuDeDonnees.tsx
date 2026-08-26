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

  let etiquette: string;
  let texte: string;
  if (jeu.synthetique) {
    etiquette = "Données de démonstration";
    texte = compteurs
      ? `Aucune donnée réelle importée — ${sourcesImportManuel} source(s) en attente d'import manuel`
      : `Aucune donnée réelle importée — corpus de démonstration (${jeu.fichiers.join(", ")})`;
  } else {
    etiquette = "Données réelles";
    texte = compteurs
      ? `${sourcesReelles} source(s) avec données réelles — ${sourcesImportManuel} source(s) en attente d'import manuel`
      : `Interactions réellement collectées (${jeu.fichiers.join(", ")})`;
  }

  return (
    <p
      role="note"
      className="flex items-center gap-2 text-xs text-ardoise-500 dark:text-ardoise-400"
    >
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 shrink-0 rounded-full ${
          jeu.synthetique ? "bg-teal-500" : "bg-emerald-600"
        }`}
      />
      <span>
        <span
          className={
            jeu.synthetique
              ? "font-medium text-ardoise-600 dark:text-ardoise-300"
              : "font-medium text-emerald-700 dark:text-emerald-400"
          }
        >
          {etiquette}
        </span>
        {" — "}
        {texte}
      </span>
    </p>
  );
}
