import { Carte, TitreCarte } from "./ui/Carte";
import type { Methode } from "@/lib/types";

/** Fiche descriptive d'une méthode de classification automatique. */
export function FicheMethode({ methode }: { methode: Methode }) {
  return (
    <Carte>
      <TitreCarte description="Description exacte du dispositif utilisé, de ses langues et de ses limites.">
        Méthode employée
      </TitreCarte>
      <dl className="space-y-2 text-sm">
        <div>
          <dt className="text-xs text-ardoise-500 dark:text-ardoise-400">Nom</dt>
          <dd className="text-ardoise-800 dark:text-ardoise-200">{methode.nom}</dd>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-xs text-ardoise-500 dark:text-ardoise-400">Version</dt>
            <dd className="text-ardoise-800 dark:text-ardoise-200">{methode.version}</dd>
          </div>
          <div>
            <dt className="text-xs text-ardoise-500 dark:text-ardoise-400">Type</dt>
            <dd className="text-ardoise-800 dark:text-ardoise-200">{methode.type}</dd>
          </div>
        </div>
        <div>
          <dt className="text-xs text-ardoise-500 dark:text-ardoise-400">Langues couvertes</dt>
          <dd className="text-ardoise-800 dark:text-ardoise-200">
            {methode.langues.join(", ")}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-ardoise-500 dark:text-ardoise-400">
            Performance évaluée
          </dt>
          <dd className="text-ardoise-800 dark:text-ardoise-200">
            {methode.performance_evaluee
              ? "oui"
              : "non — aucune mesure de précision, de rappel ou de F1 n'est annoncée"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-ardoise-500 dark:text-ardoise-400">Limites</dt>
          <dd>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-ardoise-700 dark:text-ardoise-300">
              {methode.limites.map((limite) => (
                <li key={limite}>{limite}</li>
              ))}
            </ul>
          </dd>
        </div>
        {methode.remplacable ? (
          <div>
            <dt className="text-xs text-ardoise-500 dark:text-ardoise-400">Remplaçabilité</dt>
            <dd className="text-ardoise-700 dark:text-ardoise-300">{methode.remplacable}</dd>
          </div>
        ) : null}
      </dl>
    </Carte>
  );
}
