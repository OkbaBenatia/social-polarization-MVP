import { dateHeure } from "@/lib/format";

export function PiedDePage({ genereLe }: { genereLe?: string | null }) {
  return (
    <footer className="mt-12 border-t border-ardoise-200 bg-white dark:border-ardoise-800 dark:bg-ardoise-950">
      <div className="mx-auto max-w-7xl px-4 py-8 text-sm text-ardoise-600 sm:px-6 dark:text-ardoise-400">
        <p className="font-medium text-ardoise-800 dark:text-ardoise-200">
          Étude de la polarisation et de la propagation du discours de haine sur les réseaux
          sociaux
        </p>
        <p className="mt-1">
          Préparation, conception et programmation : <strong>Dr. Okba Ben Atia</strong>
        </p>
        <p className="mt-3 max-w-3xl text-xs leading-relaxed">
          Ce tableau de bord restitue uniquement des résultats calculés hors ligne par le
          pipeline Python et enregistrés dans <code>public/data/</code>. Les classifications
          automatiques (sentiment, colère/soutien, toxicité) sont indicatives et n'ont fait
          l'objet d'aucune évaluation sur corpus annoté.
        </p>
        {genereLe ? (
          <p className="mt-3 text-xs">Résultats générés le {dateHeure(genereLe)}.</p>
        ) : null}
      </div>
    </footer>
  );
}
