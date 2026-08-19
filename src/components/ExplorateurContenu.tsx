"use client";

import { useState } from "react";

import { ListeTermes } from "./graphiques/ListeTermes";
import { Carte, TitreCarte } from "./ui/Carte";
import type { Contenu } from "@/lib/types";

/**
 * Explorateur lexical : filtre par communauté et par plateforme.
 * Tous les profils sont précalculés par le pipeline Python.
 */
export function ExplorateurContenu({ donnees }: { donnees: Contenu }) {
  const [communaute, setCommunaute] = useState("toutes");
  const [plateforme, setPlateforme] = useState("toutes");

  const profil = donnees.profils[`${communaute}|${plateforme}`];

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-ardoise-200 bg-white p-4 dark:border-ardoise-800 dark:bg-ardoise-900">
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium text-ardoise-600 dark:text-ardoise-400">
              Communauté
            </span>
            <select
              value={communaute}
              onChange={(evenement) => setCommunaute(evenement.target.value)}
              className="w-full rounded-md border border-ardoise-300 bg-white px-3 py-2 text-sm text-ardoise-800 focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600 dark:border-ardoise-700 dark:bg-ardoise-950 dark:text-ardoise-100"
            >
              {donnees.communautes.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.nom}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-xs font-medium text-ardoise-600 dark:text-ardoise-400">
              Plateforme
            </span>
            <select
              value={plateforme}
              onChange={(evenement) => setPlateforme(evenement.target.value)}
              className="w-full rounded-md border border-ardoise-300 bg-white px-3 py-2 text-sm text-ardoise-800 focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600 dark:border-ardoise-700 dark:bg-ardoise-950 dark:text-ardoise-100"
            >
              {donnees.plateformes.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.nom}
                </option>
              ))}
            </select>
          </label>
        </div>
        <p className="mt-3 text-xs text-ardoise-500 dark:text-ardoise-400">
          {profil
            ? `${profil.messages_avec_texte} message(s) textuel(s) dans cette sélection.`
            : "Sélection indisponible dans les résultats générés."}
        </p>
      </div>

      {!profil || profil.messages_avec_texte === 0 ? (
        <div className="rounded-lg border border-dashed border-ardoise-300 bg-white p-8 text-center text-sm text-ardoise-500 dark:border-ardoise-700 dark:bg-ardoise-900 dark:text-ardoise-400">
          {profil?.message ??
            "Aucun contenu textuel ne correspond à cette combinaison de filtres."}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <Carte>
            <TitreCarte description="Fréquences brutes après suppression des mots vides.">
              Mots les plus fréquents
            </TitreCarte>
            <ListeTermes
              termes={profil.mots.map((element) => ({
                terme: element.terme,
                valeur: element.occurrences,
              }))}
            />
          </Carte>

          <Carte>
            <TitreCarte description="Suites de deux mots consécutifs les plus fréquentes.">
              Bigrammes
            </TitreCarte>
            <ListeTermes
              termes={profil.bigrammes.map((element) => ({
                terme: element.terme,
                valeur: element.occurrences,
              }))}
              vide="Aucun bigramme n'a pu être extrait de cette sélection."
            />
          </Carte>

          <Carte>
            <TitreCarte description="Termes les plus caractéristiques au sens de la pondération TF-IDF.">
              Termes caractéristiques (TF-IDF)
            </TitreCarte>
            <ListeTermes
              termes={profil.tfidf.map((element) => ({
                terme: element.terme,
                valeur: element.score,
              }))}
              unite="score"
              vide="Corpus trop réduit pour un calcul TF-IDF fiable sur cette sélection."
            />
          </Carte>

          <Carte>
            <TitreCarte description="Hashtags relevés dans les messages de la sélection.">
              Hashtags
            </TitreCarte>
            <ListeTermes
              termes={profil.hashtags.map((element) => ({
                terme: element.terme,
                valeur: element.occurrences,
              }))}
              vide="Aucun hashtag n'apparaît dans cette sélection."
            />
          </Carte>
        </div>
      )}
    </div>
  );
}
