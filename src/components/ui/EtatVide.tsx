import Link from "next/link";

/**
 * Message affiché lorsqu'un fichier de résultats est absent ou vide.
 * Aucune donnée n'est inventée : l'utilisateur est renvoyé vers le pipeline.
 */
export function EtatVide({
  titre = "Aucun résultat disponible",
  message,
  fichier,
}: {
  titre?: string;
  message?: string;
  fichier?: string;
}) {
  return (
    <div className="rounded-lg border border-dashed border-ardoise-300 bg-white p-8 text-center dark:border-ardoise-700 dark:bg-ardoise-900">
      <h2 className="text-lg font-semibold text-ardoise-800 dark:text-ardoise-100">{titre}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm text-ardoise-600 dark:text-ardoise-400">
        {message ??
          "Les résultats n'ont pas encore été générés, ou le fichier attendu est introuvable."}
      </p>
      {fichier ? (
        <p className="mt-2 font-mono text-xs text-ardoise-500 dark:text-ardoise-500">
          Fichier attendu : public/data/{fichier}
        </p>
      ) : null}
      <div className="mt-5 rounded-md bg-ardoise-50 p-4 text-left dark:bg-ardoise-950">
        <p className="text-xs font-medium text-ardoise-700 dark:text-ardoise-300">
          Pour générer les résultats :
        </p>
        <pre className="mt-2 overflow-x-auto text-xs text-ardoise-600 dark:text-ardoise-400">
          <code>python analysis/run_analysis.py</code>
        </pre>
      </div>
      <Link
        href="/methodologie"
        className="mt-5 inline-block text-sm font-medium text-teal-700 underline-offset-4 hover:underline dark:text-teal-400"
      >
        Consulter la méthodologie
      </Link>
    </div>
  );
}
