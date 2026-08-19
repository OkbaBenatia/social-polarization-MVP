import type { ReactNode } from "react";

export function Carte({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-lg border border-ardoise-200 bg-white p-5 shadow-sm dark:border-ardoise-800 dark:bg-ardoise-900 ${className}`}
    >
      {children}
    </div>
  );
}

export function TitreCarte({
  children,
  description,
}: {
  children: ReactNode;
  description?: ReactNode;
}) {
  return (
    <div className="mb-4">
      <h3 className="text-base font-semibold text-ardoise-800 dark:text-ardoise-100">
        {children}
      </h3>
      {description ? (
        <p className="mt-1 text-sm text-ardoise-500 dark:text-ardoise-400">{description}</p>
      ) : null}
    </div>
  );
}
