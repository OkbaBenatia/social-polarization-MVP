import type { Metadata } from "next";

import "./globals.css";

import { NavigationPrincipale } from "@/components/NavigationPrincipale";
import { PiedDePage } from "@/components/PiedDePage";
import { lireOverview } from "@/lib/data";

export const metadata: Metadata = {
  title: {
    default:
      "Polarisation et discours de haine sur les réseaux sociaux",
    template: "%s — Polarisation et discours de haine",
  },
  description:
    "MVP académique d'analyse de la polarisation, des communautés et de la propagation du discours de haine sur les réseaux sociaux. Préparation, conception et programmation : Dr. Okba Ben Atia.",
  authors: [{ name: "Dr. Okba Ben Atia" }],
};

// Applique la préférence de thème avant le premier rendu (évite le clignotement).
const SCRIPT_THEME = `
(function () {
  try {
    var pref = window.localStorage.getItem('theme-polarisation');
    var systeme = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (pref === 'sombre' || (!pref && systeme)) {
      document.documentElement.classList.add('dark');
    }
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const overview = lireOverview();

  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: SCRIPT_THEME }} />
      </head>
      <body className="min-h-screen">
        <a
          href="#contenu-principal"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-white focus:px-4 focus:py-2 focus:text-sm dark:focus:bg-ardoise-900"
        >
          Aller au contenu principal
        </a>
        <NavigationPrincipale />
        <main id="contenu-principal" className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
          {children}
        </main>
        <PiedDePage genereLe={overview?.genere_le} />
      </body>
    </html>
  );
}
