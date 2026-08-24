import { Carte } from "./Carte";

/**
 * Carte d'indicateur. Structure uniforme en trois rangées — titre, valeur,
 * précision — avec des hauteurs de rangée fixes : toutes les valeurs
 * principales s'alignent donc exactement, quelle que soit la longueur du
 * titre ou la présence d'une précision.
 */
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
    <Carte className="flex h-full flex-col gap-1.5">
      <p className="min-h-[3rem] text-xs font-medium uppercase leading-4 tracking-wide text-ardoise-500 dark:text-ardoise-400">
        {libelle}
      </p>
      <p className="text-2xl font-semibold leading-8 tabular-nums text-ardoise-900 dark:text-white">
        {valeur}
      </p>
      <p className="min-h-[1rem] text-xs leading-4 text-ardoise-500 dark:text-ardoise-400">
        {precision ?? ""}
      </p>
    </Carte>
  );
}
