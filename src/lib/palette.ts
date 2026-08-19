/** Palette du tableau de bord : blanc, gris clair, bleu ardoise, teal discret. */

/** Teintes lisibles sur fond clair comme sur fond sombre. */
export const COULEURS_COMMUNAUTES = [
  "#64748b", // ardoise
  "#0d9488", // teal
  "#a3b1c6", // ardoise clair
  "#14b8a6", // teal clair
  "#475569",
  "#2dd4bf",
  "#7c8ba1",
  "#0f766e",
];

/** Variante éclaircie, utilisée sur le fond très sombre du graphe. */
export const COULEURS_COMMUNAUTES_SOMBRE = [
  "#94a3b8",
  "#14b8a6",
  "#cbd5e1",
  "#5eead4",
  "#64748b",
  "#99f6e4",
  "#e2e8f0",
  "#2dd4bf",
];

export function couleurCommunaute(identifiant: number, sombre = false): string {
  const palette = sombre ? COULEURS_COMMUNAUTES_SOMBRE : COULEURS_COMMUNAUTES;
  if (identifiant <= 0) return sombre ? "#475569" : "#cbd5e1";
  return palette[(identifiant - 1) % palette.length];
}

export const COULEURS_SENTIMENT: Record<string, string> = {
  Positif: "#0d9488",
  Neutre: "#94a3b8",
  Négatif: "#475569",
};

export const COULEURS_EMOTIONS: Record<string, string> = {
  "Colère": "#475569",
  "Soutien / approbation": "#0d9488",
  "Autre / neutre": "#cbd5e1",
};

export const COULEURS_HAINE: Record<string, string> = {
  "Non haineux": "#cbd5e1",
  "Toxique / offensant": "#64748b",
  "Potentiellement haineux": "#0f172a",
};

export const COULEURS_PLATEFORMES: Record<string, string> = {
  facebook: "#475569",
  x: "#0f172a",
  instagram: "#0d9488",
};

export function couleurCategorie(
  categorie: string,
  table: Record<string, string>,
  index = 0,
): string {
  return table[categorie] ?? COULEURS_COMMUNAUTES[index % COULEURS_COMMUNAUTES.length];
}

/** Couleurs dépendantes du thème, utilisées par les graphiques et le réseau. */
export function couleursTheme(sombre: boolean) {
  return {
    texte: sombre ? "#cbd5e1" : "#334155",
    texteAttenue: sombre ? "#94a3b8" : "#64748b",
    grille: sombre ? "#1e293b" : "#e2e8f0",
    fond: sombre ? "#111a2b" : "#ffffff",
    fondPage: sombre ? "#080f1d" : "#f8fafc",
    bordure: sombre ? "#1e293b" : "#e2e8f0",
    lien: sombre ? "#334155" : "#cbd5e1",
    lienInter: sombre ? "#0d9488" : "#14b8a6",
  };
}
