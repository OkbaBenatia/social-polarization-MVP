"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { couleursTheme } from "@/lib/palette";
import { useThemeSombre } from "@/lib/theme";

export function GraphiqueCamembert({
  donnees,
  hauteur = 280,
}: {
  donnees: { nom: string; valeur: number; couleur: string }[];
  hauteur?: number;
}) {
  const sombre = useThemeSombre();
  const couleurs = couleursTheme(sombre);
  const total = donnees.reduce((somme, element) => somme + element.valeur, 0);

  if (!total) {
    return (
      <p className="py-8 text-center text-sm text-ardoise-500 dark:text-ardoise-400">
        Aucune donnée à représenter.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={hauteur}>
      <PieChart>
        <Pie
          data={donnees}
          dataKey="valeur"
          nameKey="nom"
          innerRadius="52%"
          outerRadius="80%"
          paddingAngle={2}
          stroke={couleurs.fond}
        >
          {donnees.map((element) => (
            <Cell key={element.nom} fill={element.couleur} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: couleurs.fond,
            border: `1px solid ${couleurs.bordure}`,
            borderRadius: 6,
            fontSize: 12,
            color: couleurs.texte,
          }}
          formatter={(valeur: number, nom: string) => [
            `${valeur} (${((valeur / total) * 100).toFixed(1).replace(".", ",")} %)`,
            nom,
          ]}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: couleurs.texte }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
