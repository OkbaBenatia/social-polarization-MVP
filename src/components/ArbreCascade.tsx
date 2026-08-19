"use client";

import { useMemo, useState } from "react";

import { couleurCommunaute } from "@/lib/palette";
import { dateHeure, nomTypeInteraction } from "@/lib/format";
import type { Cascade, NoeudCascade } from "@/lib/types";

/**
 * Visualisation simple d'une cascade : arbre indenté par profondeur.
 * Volontairement lisible plutôt que spectaculaire.
 */
export function ArbreCascade({
  cascades,
  arbres,
  noeudsMax,
}: {
  cascades: Cascade[];
  arbres: Record<string, NoeudCascade[]>;
  noeudsMax: number;
}) {
  const disponibles = cascades.filter((cascade) => arbres[cascade.cascade_id]?.length);
  const [selection, setSelection] = useState(disponibles[0]?.cascade_id ?? "");

  const noeuds = useMemo(() => arbres[selection] ?? [], [arbres, selection]);
  const cascade = cascades.find((element) => element.cascade_id === selection);

  const parProfondeur = useMemo(() => {
    const groupes = new Map<number, NoeudCascade[]>();
    noeuds.forEach((noeud) => {
      const liste = groupes.get(noeud.profondeur) ?? [];
      liste.push(noeud);
      groupes.set(noeud.profondeur, liste);
    });
    return [...groupes.entries()].sort((a, b) => a[0] - b[0]);
  }, [noeuds]);

  if (!disponibles.length) {
    return (
      <p className="text-sm text-ardoise-500 dark:text-ardoise-400">
        Aucun arbre de cascade détaillé n'a été produit pour ce jeu de données.
      </p>
    );
  }

  const ETIQUETTES_PROFONDEUR = [
    "Publication",
    "Commentaires",
    "Réponses (niveau 1)",
    "Réponses (niveau 2)",
    "Réponses (niveau 3)",
  ];

  return (
    <div className="space-y-4">
      <label className="block text-sm">
        <span className="mb-1 block text-xs font-medium text-ardoise-600 dark:text-ardoise-400">
          Cascade
        </span>
        <select
          value={selection}
          onChange={(evenement) => setSelection(evenement.target.value)}
          className="w-full max-w-md rounded-md border border-ardoise-300 bg-white px-3 py-2 text-sm text-ardoise-800 focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600 dark:border-ardoise-700 dark:bg-ardoise-950 dark:text-ardoise-100"
        >
          {disponibles.map((element) => (
            <option key={element.cascade_id} value={element.cascade_id}>
              {element.cascade_id} — {element.source_id} — {element.taille} interactions
            </option>
          ))}
        </select>
      </label>

      {cascade ? (
        <p className="text-xs text-ardoise-500 dark:text-ardoise-400">
          Profondeur {cascade.profondeur} · {cascade.participants} participants ·{" "}
          {cascade.nombre_communautes_atteintes} communauté(s) traversée(s)
          {noeuds.length < cascade.taille
            ? ` · arbre limité aux ${noeudsMax} premières interactions sur ${cascade.taille}`
            : ""}
        </p>
      ) : null}

      <div className="space-y-4">
        {parProfondeur.map(([profondeur, liste]) => (
          <div key={profondeur}>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ardoise-500 dark:text-ardoise-400">
              Niveau {profondeur} —{" "}
              {ETIQUETTES_PROFONDEUR[profondeur] ?? `Réponses (niveau ${profondeur - 1})`}{" "}
              <span className="font-normal normal-case">({liste.length})</span>
            </p>
            <div
              className="flex flex-wrap gap-1.5"
              style={{ paddingLeft: `${Math.min(profondeur, 4) * 12}px` }}
            >
              {liste.map((noeud) => (
                <span
                  key={noeud.id}
                  title={`${noeud.auteur} · ${noeud.communaute} · ${nomTypeInteraction(
                    noeud.type,
                  )} · ${noeud.sentiment} · ${noeud.emotion} · ${noeud.haine_label}${
                    noeud.horodatage ? ` · ${dateHeure(noeud.horodatage)}` : ""
                  }`}
                  className="flex items-center gap-1.5 rounded border border-ardoise-200 bg-white px-2 py-1 text-xs text-ardoise-700 dark:border-ardoise-800 dark:bg-ardoise-950 dark:text-ardoise-300"
                >
                  <span
                    aria-hidden="true"
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: couleurCommunaute(noeud.communaute_id) }}
                  />
                  {nomTypeInteraction(noeud.type)}
                  {noeud.haine_label !== "Non haineux" ? (
                    <span
                      aria-label={noeud.haine_label}
                      className="rounded bg-ardoise-900 px-1 text-[10px] text-white dark:bg-ardoise-200 dark:text-ardoise-900"
                    >
                      {noeud.haine_label === "Potentiellement haineux" ? "PH" : "TO"}
                    </span>
                  ) : null}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-ardoise-500 dark:text-ardoise-400">
        Couleur : communauté de l'auteur. « PH » : contenu classé potentiellement haineux ;
        « TO » : contenu classé toxique ou offensant. Survolez un élément pour le détail.
      </p>
    </div>
  );
}
