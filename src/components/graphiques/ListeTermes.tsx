/** Liste de termes avec barre de proportion — lisible et sans dépendance graphique. */
export function ListeTermes({
  termes,
  unite = "occurrences",
  vide = "Aucun terme disponible pour cette sélection.",
}: {
  termes: { terme: string; valeur: number }[];
  unite?: string;
  vide?: string;
}) {
  if (!termes.length) {
    return <p className="text-sm text-ardoise-500 dark:text-ardoise-400">{vide}</p>;
  }
  const maximum = Math.max(...termes.map((element) => element.valeur), 1);

  return (
    <ol className="space-y-1.5">
      {termes.map((element, index) => (
        <li key={`${element.terme}-${index}`} className="text-sm">
          <div className="flex items-baseline justify-between gap-3">
            <span className="truncate text-ardoise-800 dark:text-ardoise-200" dir="auto">
              <span className="mr-2 text-xs tabular-nums text-ardoise-400">{index + 1}.</span>
              {element.terme}
            </span>
            <span
              className="shrink-0 tabular-nums text-xs text-ardoise-500 dark:text-ardoise-400"
              title={unite}
            >
              {unite === "occurrences"
                ? element.valeur
                : element.valeur.toFixed(3).replace(".", ",")}
            </span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-ardoise-100 dark:bg-ardoise-800">
            <div
              className="h-full rounded-full bg-teal-600 dark:bg-teal-500"
              style={{ width: `${Math.max(3, (element.valeur / maximum) * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ol>
  );
}
