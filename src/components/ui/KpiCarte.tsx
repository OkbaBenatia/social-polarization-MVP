import { Carte } from "./Carte";

export function KpiCarte({
  libelle,
  valeur,
  precision,
}: {
  libelle: string;
  valeur: string;
  precision?: string;
}) {
  return (
    <Carte className="flex flex-col justify-between">
      <p className="text-xs font-medium uppercase tracking-wide text-ardoise-500 dark:text-ardoise-400">
        {libelle}
      </p>
      <p className="mt-2 text-2xl font-semibold tabular-nums text-ardoise-900 dark:text-white">
        {valeur}
      </p>
      {precision ? (
        <p className="mt-1 text-xs text-ardoise-500 dark:text-ardoise-400">{precision}</p>
      ) : null}
    </Carte>
  );
}
