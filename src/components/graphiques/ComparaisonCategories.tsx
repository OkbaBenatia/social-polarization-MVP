"use client";

import { useState } from "react";

import { GraphiqueBarres } from "./GraphiqueBarres";
import { couleurCategorie } from "@/lib/palette";
import type { LigneDimension } from "@/lib/types";

/**
 * Comparaison d'une classification catégorielle selon une dimension
 * (communauté, plateforme, source). Les valeurs proviennent intégralement des
 * fichiers JSON produits par le pipeline.
 */
export function ComparaisonCategories({
  lignes,
  categories,
  couleurs,
  hauteur = 320,
  libelleDimension = "Catégorie",
}: {
  lignes: LigneDimension[];
  categories: string[];
  couleurs: Record<string, string>;
  hauteur?: number;
  libelleDimension?: string;
}) {
  const [relatif, setRelatif] = useState(true);

  if (!lignes.length) {
    return (
      <p className="py-8 text-center text-sm text-ardoise-500 dark:text-ardoise-400">
        Aucune donnée disponible pour cette comparaison.
      </p>
    );
  }

  const donnees = lignes.map((ligne) => {
    const element: Record<string, unknown> = { dimension: ligne.libelle };
    categories.forEach((categorie) => {
      element[categorie] = relatif
        ? Number(ligne[`part_${categorie}`] ?? 0)
        : Number(ligne[categorie] ?? 0);
    });
    return element;
  });

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-ardoise-500 dark:text-ardoise-400">
          {libelleDimension} — {relatif ? "proportions" : "effectifs"}
        </p>
        <div
          className="inline-flex overflow-hidden rounded-md border border-ardoise-300 text-xs dark:border-ardoise-700"
          role="group"
          aria-label="Mode d'affichage"
        >
          <button
            type="button"
            onClick={() => setRelatif(true)}
            aria-pressed={relatif}
            className={`px-3 py-1.5 font-medium transition-colors ${
              relatif
                ? "bg-ardoise-700 text-white dark:bg-ardoise-200 dark:text-ardoise-900"
                : "bg-white text-ardoise-600 hover:bg-ardoise-100 dark:bg-ardoise-950 dark:text-ardoise-300 dark:hover:bg-ardoise-800"
            }`}
          >
            Proportions
          </button>
          <button
            type="button"
            onClick={() => setRelatif(false)}
            aria-pressed={!relatif}
            className={`px-3 py-1.5 font-medium transition-colors ${
              !relatif
                ? "bg-ardoise-700 text-white dark:bg-ardoise-200 dark:text-ardoise-900"
                : "bg-white text-ardoise-600 hover:bg-ardoise-100 dark:bg-ardoise-950 dark:text-ardoise-300 dark:hover:bg-ardoise-800"
            }`}
          >
            Effectifs
          </button>
        </div>
      </div>

      <GraphiqueBarres
        donnees={donnees}
        cleAxe="dimension"
        empile
        hauteur={hauteur}
        series={categories.map((categorie, index) => ({
          cle: categorie,
          libelle: categorie,
          couleur: couleurCategorie(categorie, couleurs, index),
        }))}
        format={relatif ? "pourcentage" : "nombre"}
        libelleAxeValeur={relatif ? "Part des messages" : "Nombre de messages"}
      />
    </div>
  );
}
