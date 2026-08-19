/** Formatage des valeurs affichées (locale française). */

export function nombre(valeur: number | null | undefined): string {
  if (valeur === null || valeur === undefined || Number.isNaN(valeur)) return "—";
  return new Intl.NumberFormat("fr-FR").format(valeur);
}

export function pourcentage(part: number | null | undefined, decimales = 1): string {
  if (part === null || part === undefined || Number.isNaN(part)) return "—";
  return `${(part * 100).toFixed(decimales).replace(".", ",")} %`;
}

export function decimal(valeur: number | null | undefined, decimales = 3): string {
  if (valeur === null || valeur === undefined || Number.isNaN(valeur)) return "—";
  return valeur.toFixed(decimales).replace(".", ",");
}

export function dateCourte(valeur: string | null | undefined): string {
  if (!valeur) return "—";
  const date = new Date(valeur);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(date);
}

export function dateHeure(valeur: string | null | undefined): string {
  if (!valeur) return "—";
  const date = new Date(valeur);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function duree(minutes: number | null | undefined): string {
  if (minutes === null || minutes === undefined || Number.isNaN(minutes)) return "—";
  if (minutes < 60) return `${Math.round(minutes)} min`;
  const heures = minutes / 60;
  if (heures < 48) return `${heures.toFixed(1).replace(".", ",")} h`;
  return `${(heures / 24).toFixed(1).replace(".", ",")} j`;
}

export function nomPlateforme(plateforme: string): string {
  const noms: Record<string, string> = {
    facebook: "Facebook",
    x: "X",
    instagram: "Instagram",
  };
  return noms[plateforme] ?? plateforme.charAt(0).toUpperCase() + plateforme.slice(1);
}

export function nomTypeInteraction(type: string): string {
  const noms: Record<string, string> = {
    post: "Publication",
    comment: "Commentaire",
    reply: "Réponse",
    mention: "Mention",
    share: "Partage",
    repost: "Repost",
    quote: "Citation",
  };
  return noms[type] ?? type;
}
