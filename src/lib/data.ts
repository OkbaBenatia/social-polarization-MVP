import fs from "node:fs";
import path from "node:path";

import type {
  Communautes,
  Contenu,
  DiscoursHaineux,
  AnalyseCategorielle,
  Overview,
  Propagation,
  Reseau,
  Sources,
} from "./types";

const REPERTOIRE_DONNEES = path.join(process.cwd(), "public", "data");

/**
 * Lit un fichier de résultats produit par le pipeline Python.
 *
 * Retourne `null` si le fichier est absent ou illisible : chaque page affiche
 * alors un message explicite en français plutôt que de planter.
 */
export function lireResultats<T>(nom: string): T | null {
  try {
    const contenu = fs.readFileSync(path.join(REPERTOIRE_DONNEES, nom), "utf-8");
    const donnees = JSON.parse(contenu) as T;
    return donnees;
  } catch {
    return null;
  }
}

export const lireOverview = () => lireResultats<Overview>("overview.json");
export const lireSources = () => lireResultats<Sources>("sources.json");
export const lireReseau = () => lireResultats<Reseau>("network.json");
export const lireCommunautes = () => lireResultats<Communautes>("communities.json");
export const lireContenu = () => lireResultats<Contenu>("content.json");
export const lireSentiment = () => lireResultats<AnalyseCategorielle>("sentiment.json");
export const lireEmotions = () => lireResultats<AnalyseCategorielle>("emotions.json");
export const lireDiscoursHaineux = () => lireResultats<DiscoursHaineux>("hate_speech.json");
export const lirePropagation = () => lireResultats<Propagation>("propagation.json");
