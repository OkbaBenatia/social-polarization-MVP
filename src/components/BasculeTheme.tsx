"use client";

import { useEffect, useState } from "react";

const CLE_STOCKAGE = "theme-polarisation";

export function BasculeTheme() {
  const [sombre, setSombre] = useState<boolean | null>(null);

  useEffect(() => {
    setSombre(document.documentElement.classList.contains("dark"));
  }, []);

  const basculer = () => {
    const racine = document.documentElement;
    const nouveau = !racine.classList.contains("dark");
    racine.classList.toggle("dark", nouveau);
    try {
      window.localStorage.setItem(CLE_STOCKAGE, nouveau ? "sombre" : "clair");
    } catch {
      /* stockage indisponible : la préférence n'est simplement pas mémorisée */
    }
    setSombre(nouveau);
  };

  return (
    <button
      type="button"
      onClick={basculer}
      aria-label={sombre ? "Activer le mode clair" : "Activer le mode sombre"}
      title={sombre ? "Mode clair" : "Mode sombre"}
      className="rounded-md border border-ardoise-200 px-3 py-2 text-sm font-medium text-ardoise-700 transition-colors hover:bg-ardoise-100 dark:border-ardoise-700 dark:text-ardoise-200 dark:hover:bg-ardoise-800"
    >
      {sombre === null ? "Thème" : sombre ? "Clair" : "Sombre"}
    </button>
  );
}
