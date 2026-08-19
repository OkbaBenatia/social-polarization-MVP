import type { ReactNode } from "react";

export function EntetePage({
  titre,
  description,
  children,
}: {
  titre: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <header className="mb-6">
      <h1 className="text-2xl font-semibold tracking-tight text-ardoise-900 dark:text-white sm:text-3xl">
        {titre}
      </h1>
      {description ? (
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ardoise-600 dark:text-ardoise-400">
          {description}
        </p>
      ) : null}
      {children ? <div className="mt-4">{children}</div> : null}
    </header>
  );
}
