import { pourcentage } from "@/lib/format";
import { couleurCategorie } from "@/lib/palette";
import type { Repartition } from "@/lib/types";

/** Barre de répartition compacte, utilisée dans les fiches de communauté. */
export function RepartitionCompacte({
  titre,
  repartition,
  couleurs,
}: {
  titre: string;
  repartition: Repartition[];
  couleurs: Record<string, string>;
}) {
  const total = repartition.reduce((somme, element) => somme + element.nombre, 0);

  return (
    <div>
      <p className="text-xs font-medium text-ardoise-600 dark:text-ardoise-400">{titre}</p>
      {total === 0 ? (
        <p className="mt-1 text-xs text-ardoise-500 dark:text-ardoise-500">
          Aucun message textuel classé.
        </p>
      ) : (
        <>
          <div className="mt-1.5 flex h-2.5 overflow-hidden rounded-full bg-ardoise-100 dark:bg-ardoise-800">
            {repartition.map((element, index) => (
              <div
                key={element.categorie}
                style={{
                  width: `${element.part * 100}%`,
                  backgroundColor: couleurCategorie(element.categorie, couleurs, index),
                }}
                title={`${element.categorie} : ${element.nombre} (${pourcentage(element.part)})`}
              />
            ))}
          </div>
          <ul className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs text-ardoise-600 dark:text-ardoise-400">
            {repartition.map((element, index) => (
              <li key={element.categorie} className="flex items-center gap-1.5">
                <span
                  aria-hidden="true"
                  className="h-2 w-2 rounded-full"
                  style={{
                    backgroundColor: couleurCategorie(element.categorie, couleurs, index),
                  }}
                />
                {element.categorie} {pourcentage(element.part, 0)}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
