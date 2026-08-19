import type { ReactNode } from "react";

type Ton = "neutre" | "teal" | "ardoise" | "attention" | "sombre";

const TONS: Record<Ton, string> = {
  neutre:
    "bg-ardoise-100 text-ardoise-700 dark:bg-ardoise-800 dark:text-ardoise-200",
  teal: "bg-teal-600/10 text-teal-700 dark:bg-teal-400/10 dark:text-teal-300",
  ardoise:
    "bg-ardoise-600/10 text-ardoise-700 dark:bg-ardoise-400/10 dark:text-ardoise-200",
  attention:
    "bg-amber-500/10 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300",
  sombre: "bg-ardoise-900 text-white dark:bg-ardoise-100 dark:text-ardoise-900",
};

export function Badge({ children, ton = "neutre" }: { children: ReactNode; ton?: Ton }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${TONS[ton]}`}
    >
      {children}
    </span>
  );
}

/** Ton associé au statut de collecte d'une source. */
export function tonStatut(statut: string): Ton {
  switch (statut) {
    case "Données disponibles":
      return "teal";
    case "Accès partiel":
      return "attention";
    case "Données de démonstration":
      return "ardoise";
    default:
      return "neutre";
  }
}
