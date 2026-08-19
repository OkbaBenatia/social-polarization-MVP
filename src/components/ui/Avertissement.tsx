import type { ReactNode } from "react";

type Variante = "information" | "attention" | "synthetique";

const STYLES: Record<Variante, string> = {
  information:
    "border-ardoise-200 bg-ardoise-100/60 text-ardoise-700 dark:border-ardoise-800 dark:bg-ardoise-900 dark:text-ardoise-300",
  attention:
    "border-amber-300/60 bg-amber-50 text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200",
  synthetique:
    "border-teal-600/30 bg-teal-50 text-teal-900 dark:border-teal-400/30 dark:bg-teal-400/10 dark:text-teal-200",
};

export function Avertissement({
  children,
  variante = "information",
  titre,
}: {
  children: ReactNode;
  variante?: Variante;
  titre?: string;
}) {
  return (
    <div className={`rounded-md border px-4 py-3 text-sm ${STYLES[variante]}`} role="note">
      {titre ? <p className="font-semibold">{titre}</p> : null}
      <div className={titre ? "mt-1" : ""}>{children}</div>
    </div>
  );
}
