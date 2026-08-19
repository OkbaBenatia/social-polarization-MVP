import type { ReactNode } from "react";

export function Tableau({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-ardoise-200 dark:border-ardoise-800">
      <table className="w-full min-w-[640px] border-collapse text-sm">{children}</table>
    </div>
  );
}

export function EnteteTableau({ colonnes }: { colonnes: ReactNode[] }) {
  return (
    <thead className="bg-ardoise-100 text-left dark:bg-ardoise-900">
      <tr>
        {colonnes.map((colonne, index) => (
          <th
            key={index}
            scope="col"
            className="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wide text-ardoise-600 dark:text-ardoise-400"
          >
            {colonne}
          </th>
        ))}
      </tr>
    </thead>
  );
}

export function CorpsTableau({ children }: { children: ReactNode }) {
  return (
    <tbody className="divide-y divide-ardoise-200 bg-white dark:divide-ardoise-800 dark:bg-ardoise-950">
      {children}
    </tbody>
  );
}

export function Cellule({
  children,
  numerique = false,
  className = "",
}: {
  children: ReactNode;
  numerique?: boolean;
  className?: string;
}) {
  return (
    <td
      className={`px-4 py-3 align-top text-ardoise-700 dark:text-ardoise-300 ${
        numerique ? "tabular-nums" : ""
      } ${className}`}
    >
      {children}
    </td>
  );
}
