"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { pourcentage } from "@/lib/format";
import { couleursTheme } from "@/lib/palette";
import { useThemeSombre } from "@/lib/theme";

/** Format déclaratif (sérialisable) : un composant serveur ne peut pas passer de fonction. */
export type FormatValeur = "nombre" | "pourcentage";

function formater(format: FormatValeur | undefined, valeur: number): string {
  if (format === "pourcentage") return pourcentage(valeur, 0);
  return new Intl.NumberFormat("fr-FR").format(valeur);
}

export interface SerieBarres {
  cle: string;
  libelle: string;
  couleur: string;
}

export function GraphiqueBarres({
  donnees,
  cleAxe,
  series,
  empile = false,
  hauteur = 300,
  horizontal = false,
  format,
  libelleAxeValeur,
}: {
  donnees: Record<string, unknown>[];
  cleAxe: string;
  series: SerieBarres[];
  empile?: boolean;
  hauteur?: number;
  horizontal?: boolean;
  format?: FormatValeur;
  libelleAxeValeur?: string;
}) {
  const sombre = useThemeSombre();
  const couleurs = couleursTheme(sombre);

  if (!donnees.length) {
    return (
      <p className="py-8 text-center text-sm text-ardoise-500 dark:text-ardoise-400">
        Aucune donnée à représenter.
      </p>
    );
  }

  // Les axes doivent rester des enfants directs de BarChart : Recharts ne
  // parcourt pas les fragments React pour les détecter.
  const etiquettesLongues = donnees.length > 5;
  const axeCategorie = {
    type: "category" as const,
    dataKey: cleAxe,
    stroke: couleurs.texteAttenue,
    tick: { fill: couleurs.texteAttenue, fontSize: 11 },
    interval: 0 as const,
  };
  const axeValeur = {
    type: "number" as const,
    stroke: couleurs.texteAttenue,
    tick: { fill: couleurs.texteAttenue, fontSize: 11 },
    tickFormatter: (valeur: number) => formater(format, valeur),
    // Des proportions empilées totalisent 1 : l'axe est borné pour éviter un
    // maximum automatique supérieur à 100 %.
    domain: format === "pourcentage" && empile ? ([0, 1] as [number, number]) : undefined,
  };

  return (
    <ResponsiveContainer width="100%" height={hauteur}>
      <BarChart
        data={donnees}
        layout={horizontal ? "vertical" : "horizontal"}
        margin={{ top: 8, right: 16, bottom: horizontal ? 8 : etiquettesLongues ? 48 : 8, left: 4 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={couleurs.grille} vertical={horizontal} />
        <XAxis
          {...(horizontal ? axeValeur : axeCategorie)}
          angle={!horizontal && etiquettesLongues ? -25 : 0}
          textAnchor={!horizontal && etiquettesLongues ? "end" : "middle"}
          height={!horizontal && etiquettesLongues ? 60 : 28}
        />
        <YAxis
          {...(horizontal ? axeCategorie : axeValeur)}
          width={horizontal ? 140 : 56}
          label={
            libelleAxeValeur && !horizontal
              ? {
                  value: libelleAxeValeur,
                  angle: -90,
                  position: "insideLeft",
                  fontSize: 11,
                  fill: couleurs.texteAttenue,
                }
              : undefined
          }
        />
        <Tooltip
          cursor={{ fill: sombre ? "rgba(148,163,184,0.08)" : "rgba(15,23,42,0.04)" }}
          contentStyle={{
            backgroundColor: couleurs.fond,
            border: `1px solid ${couleurs.bordure}`,
            borderRadius: 6,
            fontSize: 12,
            color: couleurs.texte,
          }}
          labelStyle={{ color: couleurs.texte }}
          formatter={(valeur: number, nom: string) => [formater(format, valeur), nom]}
        />
        {series.length > 1 ? (
          <Legend wrapperStyle={{ fontSize: 12, color: couleurs.texte, paddingTop: 8 }} />
        ) : null}
        {series.map((serie) => (
          <Bar
            key={serie.cle}
            dataKey={serie.cle}
            name={serie.libelle}
            fill={serie.couleur}
            stackId={empile ? "empile" : undefined}
            radius={empile ? 0 : [3, 3, 0, 0]}
            maxBarSize={horizontal ? 22 : 56}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
