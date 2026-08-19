"use client";

import { useEffect, useState } from "react";

/** Indique si le thème sombre est actif (classe `dark` sur <html>). */
export function useThemeSombre(): boolean {
  const [sombre, setSombre] = useState(false);

  useEffect(() => {
    const racine = document.documentElement;
    const lire = () => setSombre(racine.classList.contains("dark"));
    lire();
    const observateur = new MutationObserver(lire);
    observateur.observe(racine, { attributes: true, attributeFilter: ["class"] });
    return () => observateur.disconnect();
  }, []);

  return sombre;
}
