"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { couleursTheme } from "@/lib/palette";
import { useThemeSombre } from "@/lib/theme";

export function GraphiqueLignes({
  donnees,
  cleAxe,
  series,
  hauteur = 280,
}: {
  donnees: Record<string, unknown>[];
  cleAxe: string;
  series: { cle: string; libelle: string; couleur: string }[];
  hauteur?: number;
}) {
  const sombre = useThemeSombre();
  const couleurs = couleursTheme(sombre);

  if (!donnees.length) {
    return (
      <p className="py-8 text-center text-sm text-ardoise-500 dark:text-ardoise-400">
        Aucune donnée temporelle disponible : les horodatages sont absents ou invalides.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={hauteur}>
      <LineChart data={donnees} margin={{ top: 8, right: 12, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={couleurs.grille} />
        <XAxis
          dataKey={cleAxe}
          stroke={couleurs.texteAttenue}
          tick={{ fill: couleurs.texteAttenue, fontSize: 11 }}
        />
        <YAxis
          stroke={couleurs.texteAttenue}
          tick={{ fill: couleurs.texteAttenue, fontSize: 11 }}
          allowDecimals={false}
          width={48}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: couleurs.fond,
            border: `1px solid ${couleurs.bordure}`,
            borderRadius: 6,
            fontSize: 12,
            color: couleurs.texte,
          }}
          labelStyle={{ color: couleurs.texte }}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: couleurs.texte }} />
        {series.map((serie) => (
          <Line
            key={serie.cle}
            type="monotone"
            dataKey={serie.cle}
            name={serie.libelle}
            stroke={serie.couleur}
            strokeWidth={2}
            dot={{ r: 2 }}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
